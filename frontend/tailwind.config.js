/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,svelte}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0C85B7',
        secondary: '#095E8F',
        accent: '#edd899',
        base: '#FFFFFF',
      },
      backdropBlur: {
        xs: '2px',
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(135deg, rgb(219 234 254) 0%, rgb(240 249 255) 50%, rgb(207 250 254) 100%)',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glass-lg': '0 12px 40px 0 rgba(31, 38, 135, 0.4)',
      },
      transitionDuration: {
        '150': '150ms',
      },
    },
  },
  plugins: [],
}
