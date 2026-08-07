/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#050608',
          2: '#08090d',
          3: '#0b0d13',
          4: '#11141c',
        },
        line: 'rgba(255,255,255,0.08)',
        brand: {
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        panel: 'inset 0 1px 0 0 rgba(255,255,255,0.04)',
        lolla: '0 0 0 1px rgba(255,255,255,0.06)',
        glow: '0 0 24px -6px rgba(45,212,191,0.45)',
      },
      keyframes: {
        softPing: {
          '0%': { transform: 'scale(1)', opacity: '0.9' },
          '80%,100%': { transform: 'scale(2.6)', opacity: '0' },
        },
        floaty: {
          '0%,100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: ' -400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
      animation: {
        'ping-soft': 'ping-soft 2.4s cubic-bezier(0,0,0.2,1) infinite',
        floaty: 'floaty 6s ease-in-out infinite',
        shimmer: 'shimmer 2.2s linear infinite',
      },
    },
  },
  plugins: [],
}