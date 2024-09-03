import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Germany Termin Bot',
  tagline: 'Germany Termin Bot: Simplifying your appointment bookings across Germany.',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://noworneverev.github.io/',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/germany-termin-bot/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'noworneverev', // Usually your GitHub org/user name.
  projectName: 'germany-termin-bot', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',          
          sidebarPath: './sidebars.ts',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          // editUrl:
          //   'https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/',
          
        },
        blog: false,        
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    docs: {
      sidebar: {
        hideable: true,
      },
    },
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'Germany Termin Bot',
      logo: {
        alt: 'My Site Logo',
        src: 'img/logo.png',
      },
      items: [        
        {
          href: 'https://github.com/noworneverev/germany-termin-bot',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',      
      copyright: `Made with ❤️ by <a href="https://noworneverev.github.io/" target="_blank" rel="noopener noreferrer">Yan-Ying Liao</a>`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
