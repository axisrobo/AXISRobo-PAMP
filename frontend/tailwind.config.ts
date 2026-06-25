import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // MongoDB-inspired palette
        'mdb-green': '#00ed64',
        'mdb-green-deep': '#00b545',
        'mdb-green-dark': '#00684a',
        'mdb-green-mid': '#00a35c',
        'mdb-green-soft': '#c3f0d2',
        'mdb-teal-deep': '#001e2b',
        'mdb-teal': '#003d4f',
        'mdb-teal-mid': '#00684a',

        // Category accents
        'mdb-purple': '#7b3ff2',
        'mdb-orange': '#fa6e39',
        'mdb-pink': '#f06bb8',
        'mdb-blue': '#3d4f9f',

        // Surfaces
        'mdb-canvas': '#ffffff',
        'mdb-canvas-dark': '#001e2b',
        'mdb-surface': '#f9fbfa',
        'mdb-surface-feature': '#e3fcef',
        'mdb-hairline': '#e1e5e8',

        // Text
        'mdb-ink': '#001e2b',
        'mdb-charcoal': '#1c2d38',
        'mdb-slate': '#3d4f5b',
        'mdb-steel': '#5c6c7a',
        'mdb-stone': '#7c8c9a',
        'mdb-muted': '#a8b3bc',

        // Legacy compat (keep existing classes working)
        'primary-blue': '#00ed64',
        'primary-blue-hover': '#00b545',
        'status-completed': '#00ed64',
        'status-in-progress': '#fa6e39',
        'status-draft': '#a8b3bc',
        'status-accepted': '#7b3ff2',
        'border-light': '#e1e5e8',
        'bg-gray': '#f9fbfa',
        'border-default': '#e1e5e8',
        'text-primary': '#001e2b',
        'text-secondary': '#5c6c7a',
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: ['Source Code Pro', 'JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'hero': ['4.5rem', { lineHeight: '1.1', letterSpacing: '-0.015em', fontWeight: '500' }],
        'display': ['3.5rem', { lineHeight: '1.15', letterSpacing: '-0.01em', fontWeight: '500' }],
        'h1': ['3rem', { lineHeight: '1.2', letterSpacing: '-0.005em', fontWeight: '500' }],
        'h2': ['2.25rem', { lineHeight: '1.25', letterSpacing: '-0.005em', fontWeight: '500' }],
        'h3': ['1.75rem', { lineHeight: '1.3', fontWeight: '500' }],
        'h5': ['1.125rem', { lineHeight: '1.4', fontWeight: '600' }],
      },
      width: {
        sidebar: '240px',
      },
      borderRadius: {
        'pill': '9999px',
        'card': '12px',
        'input': '8px',
      },
      spacing: {
        'section': '64px',
        'section-lg': '96px',
        'hero': '120px',
      },
      boxShadow: {
        'card': '0 1px 2px rgba(0,30,43,0.04)',
        'card-hover': '0 4px 12px rgba(0,30,43,0.08)',
        'mockup': '0 12px 24px -4px rgba(0,30,43,0.12)',
        'modal': '0 16px 48px -8px rgba(0,30,43,0.16)',
      },
    },
  },
  corePlugins: {
    preflight: false,
  },
  plugins: [],
};

export default config;
