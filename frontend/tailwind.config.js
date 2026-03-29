/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: 'var(--tg-bg)',
          secondary: 'var(--tg-secondary-bg)',
          text: 'var(--tg-text)',
          hint: 'var(--tg-hint)',
          link: 'var(--tg-link)',
          button: 'var(--tg-button)',
          buttonText: 'var(--tg-button-text)',
          accent: 'var(--tg-accent)',
        },
      },
    },
  },
  plugins: [],
}
