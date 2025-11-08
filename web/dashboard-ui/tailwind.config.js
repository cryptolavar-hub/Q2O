/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fdf4f8',
          100: '#fbe8f1',
          200: '#f7d1e3',
          300: '#f3a9cc',
          400: '#eb79ac',
          500: '#e04f8d',
          600: '#d03472',
          700: '#b52359',
          800: '#96204a',
          900: '#7d1f40',
        },
        purple: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        },
      },
      backgroundImage: {
        'gradient-main': 'linear-gradient(135deg, #FF6B9D 0%, #C44569 25%, #9B59B6 50%, #8E44AD 75%, #6C3483 100%)',
        'gradient-success': 'linear-gradient(135deg, #4CAF50 0%, #45A049 100%)',
        'gradient-warning': 'linear-gradient(135deg, #FFC107 0%, #FFA000 100%)',
        'gradient-error': 'linear-gradient(135deg, #F44336 0%, #D32F2F 100%)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

