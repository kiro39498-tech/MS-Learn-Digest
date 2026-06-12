/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ms: {
          blue: '#0078d4',
          dark: '#18181b',
          gray: '#f3f4f6',
          light: '#fdfdfd'
        }
      },
      fontFamily: {
        sans: ['"Segoe UI"', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
