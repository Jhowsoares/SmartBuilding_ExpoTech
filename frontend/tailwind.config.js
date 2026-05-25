/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Material Design 3 — dark navy palette (from Stitch design)
        'sb-bg':           '#0c1322',
        'sb-surface':      '#0c1322',
        'sb-surface-low':  '#141b2b',
        'sb-card':         '#191f2f',
        'sb-card-high':    '#232a3a',
        'sb-card-highest': '#2e3545',
        'sb-border':       '#424754',
        'sb-outline':      '#8c909f',
        'sb-primary':      '#adc6ff',
        'sb-primary-btn':  '#4d8eff',
        'sb-on-primary':   '#002e6a',
        'sb-secondary':    '#b7c8e1',
        'sb-secondary-c':  '#3a4a5f',
        'sb-on-surface':   '#dce2f7',
        'sb-on-muted':     '#c2c6d6',
        'sb-error':        '#ffb4ab',
        'sb-tertiary':     '#ffb786',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
