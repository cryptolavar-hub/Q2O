/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          pink: '#FF6B9D',
          rose: '#C44569',
          purple: '#9B59B6',
          violet: '#8E44AD',
          indigo: '#6C3483',
        },
      },
    },
  },
  plugins: [],
};

