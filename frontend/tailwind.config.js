/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sb-bg': '#111827',
        'sb-card': '#1F2937',
        'sb-border': '#374151',
      },
    },
  },
  plugins: [],
}
