import json
import re
import requests
import logging
import ddddocr
import base64
from PIL import Image
import io
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from datetime import datetime
from typing import Final
from dotenv import load_dotenv
import os
import telegram

load_dotenv()

TOKEN = os.getenv("TOKEN")

MUNICH_NOTFALL_TERMIN: Final = '@munich_notfall_termin'
MUNICH_RUPPERSTR_ANMELDUNG_TERMIN: Final = '@ruppertstr_anmeldung'
MUNICH_PASING_ANMELDUNG_TERMIN: Final = '@pasing_anmeldung'
MUNICH_LEONRODSTR_ANMELDUNG_TERMIN: Final = '@leonrodstr_anmeldung'
MUNICH_FORSTENRIEDERALLEE_ANMELDUNG_TERMIN: Final = '@forstenrieder_anmeldung'
MUNICH_RIESENFELDSTR_ANMELDUNG_TERMIN: Final = '@riesenfeldstr_anmeldung'
MUNICH_ORLEANSSTR_ANMELDUNG_TERMIN: Final = '@orleansstr_anmeldung'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('WDM').setLevel(logging.ERROR)

def get_token(session, url):
    response = session.get(url)
    try:
        token = re.search(r'FRM_CASETYPES_token" value="(.*?)"', response.text).group(1)
        return token
    except AttributeError:
        return None

def extract_available_dates(soup, buergerbuero_value):
    available_dates = []
    
    input_element = soup.find('input', {
        'type': 'button',
        'value': buergerbuero_value,
        'class': 'WEB_APPOINT_LOCATION_HEADLINE'
    })

    if input_element:
        next_sibling = input_element.find_next_sibling()
        if next_sibling:
            td_elements = next_sibling.find_all('td', class_='nat_calendar')
            for td in td_elements:
                if td.text.strip():
                    span_content = td.text.strip()
                    if span_content.startswith("Termin"):
                        date_match = re.search(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', span_content)
                        if date_match:
                            available_dates.append(date_match.group())
    
    return available_dates

def crack_captcha(captcha):
    ocr=ddddocr.DdddOcr(show_ad=False)
    start = captcha.find(',') + 1
    end = captcha.find('\')')
    image = captcha[start:end].encode('ascii')    
    return ocr.classification(base64.decodebytes(image)) 

def munich_an():    
    # url = "https://stadt.muenchen.de/terminvereinbarung_/terminvereinbarung_bb.html"
    url = "https://terminvereinbarung.muenchen.de/bba/termin/?loc=BB"

    while True:
        try:
            service = Service(ChromeDriverManager().install())
            # headless option
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--log-level=3")
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(url)

            element = driver.find_element(By.CSS_SELECTOR, "a:nth-child(4) > h3")
            element.click()

            select_element = driver.find_element("name", "CASETYPES[An- oder Ummeldung - Einzelperson]")
            select = Select(select_element)
            select.select_by_value("1")
            
            captcha_element = driver.find_element("id", "captchai")

            # Capture a screenshot of the CAPTCHA element
            captcha_screenshot = captcha_element.screenshot_as_png  
            captcha_image = Image.open(io.BytesIO(captcha_screenshot))            
            
            ocr=ddddocr.DdddOcr(show_ad=False)    
            captcha=ocr.classification(captcha_image)    
            
            captcha_element = driver.find_element(By.NAME, "captcha_code")
            captcha_element.send_keys(captcha)

            button_element = driver.find_element(By.CSS_SELECTOR, ".WEB_APPOINT_FORWARDBUTTON")
            button_element.click()
            ruppertstr_element = driver.find_element(By.ID, "bb1_link")
            break
        except NoSuchElementException as e:
            print(f"Captcha is wrong. Retrying in 1 second...")
            sleep(1)    
            driver.quit()

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')        
        
    pasing_available_dates = extract_available_dates(soup, 'Bürgerbüro Pasing')
    leonrodstr_available_dates = extract_available_dates(soup, 'Bürgerbüro Leonrodstraße')
    forstenriederallee_available_dates = extract_available_dates(soup, 'Bürgerbüro Forstenrieder Allee')        
    riesenfeldstr_available_dates = extract_available_dates(soup, 'Bürgerbüro Riesenfeldstraße')
    orleansstr_available_dates = extract_available_dates(soup, 'Bürgerbüro Orleansstraße')    

    # Bürgerbüro Ruppertstraße
    ruppertstr_element = driver.find_element(By.ID, "bb1_link")
    ruppertstr_element.click()
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')    
    ruppertstr_available_dates = extract_available_dates(soup, 'Bürgerbüro Ruppertstraße')
    driver.quit()

    return {
            "Ruppertstraße": {"available_dates": ruppertstr_available_dates},
            "Pasing": {"available_dates": pasing_available_dates},
            "Leonrodstraße": {"available_dates": leonrodstr_available_dates},
            "Forstenrieder Allee": {"available_dates": forstenriederallee_available_dates},
            "Riesenfeldstraße": {"available_dates": riesenfeldstr_available_dates},
            "Orleansstraße": {"available_dates": orleansstr_available_dates}            
        }

# res = munich_an()

def log_available_dates(res, location):
    now = datetime.now()
    if res[location]['available_dates']:
        logging.info(f"{res[location]['available_dates']} at {location} on {now.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        logging.info(f"No available slots for {location} on {now.strftime('%d/%m/%Y %H:%M:%S')}")

def notify_munich_an_termin(bot: telegram.Bot):
    res = munich_an()

    locations = [
        "Ruppertstraße",
        "Pasing",
        "Leonrodstraße",
        "Forstenrieder Allee",
        "Riesenfeldstraße",
        "Orleansstraße"
    ]

    locations = {
        "Ruppertstraße": MUNICH_RUPPERSTR_ANMELDUNG_TERMIN,
        "Pasing": MUNICH_PASING_ANMELDUNG_TERMIN,
        "Leonrodstraße": MUNICH_LEONRODSTR_ANMELDUNG_TERMIN,
        "Forstenrieder Allee": MUNICH_FORSTENRIEDERALLEE_ANMELDUNG_TERMIN,
        "Riesenfeldstraße": MUNICH_RIESENFELDSTR_ANMELDUNG_TERMIN,
        "Orleansstraße": MUNICH_ORLEANSSTR_ANMELDUNG_TERMIN        
    }

    bot = telegram.Bot(token=TOKEN)    
    for location, channel_id in locations.items():
        log_available_dates(res, location)
        if res[location]['available_dates']:
            message = f"Available slots for Bürgerbüro {location}:\n"
            for date in res[location]['available_dates']:
                message += f"{date}\n"
            bot.send_message(chat_id=channel_id, text=message)
    

# notify_munich_an_termin()

def munich_notfall_termin():
    url = "https://terminvereinbarung.muenchen.de/abh/termin/"
    session = requests.Session()

    token = get_token(session, url)

    payload = {
        'FRM_CASETYPES_token': token,
        'step': 'WEB_APPOINT_SEARCH_BY_CASETYPES',
        'CASETYPES[Notfalltermin UA 35]': 1,
    }
    response = session.post(url, payload)
    json_str = re.search(r'jsonAppoints = \'(.*?)\'', response.text).group(1)
    appointments = json.loads(json_str)['LOADBALANCER']['appoints']

    message = []
    has_appointments = False

    for date, times in appointments.items():
        if times:
            has_appointments = True
            message.append(f"Date: {date}")
            for time in times:
                message.append(f" - {time}")

    message_str = "\n".join(message)
    if has_appointments:
        logging.info(f"{'Available slots for Munich Notfall Termin: ' + message_str}")                        
        return True, message_str
    else:
        logging.info(f'{"No available slots for Munich Notfall Termin."}')
        return False, "No available slots for Munich Notfall Termin."
    

def notify_munich_notfalltermin(bot: telegram.Bot):
    is_available, res = munich_notfall_termin()
    if is_available:
        bot.send_message(chat_id=MUNICH_NOTFALL_TERMIN, text=res)


if __name__ == '__main__':
    bot = telegram.Bot(token=TOKEN)
    notify_munich_notfalltermin(bot)
    notify_munich_an_termin(bot)