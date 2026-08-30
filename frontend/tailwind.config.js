/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        razor: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0c83ff',
          600: '#0066e0',
          900: '#0b2447',
        }
      }
    },
  },
  plugins: [],
}
