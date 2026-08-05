/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: [
        './public/**/*.html',
        './src/js/**/*.js',
    ],
    theme: {
        extend: {
            colors: {
                // Brand palette
                brand: {
                    50: '#f0fafd',
                    100: '#d8f0f8',
                    200: '#aee0f2',
                    300: '#74c9e8',
                    400: '#3aadd4',
                    500: '#3B9EBF', // Primary accent
                    600: '#2A7FA0',
                    700: '#1d6280',
                    800: '#184f68',
                    900: '#164358',
                },
                // Background tokens
                surface: {
                    light: '#EFF3F8',
                    lightEnd: '#D8EAF6',
                    dark: '#0F1623',
                    darkEnd: '#162035',
                },
                // Glass tokens
                glass: {
                    lightBg: 'rgba(255,255,255,0.55)',
                    lightBorder: 'rgba(255,255,255,0.6)',
                    darkBg: 'rgba(255,255,255,0.07)',
                    darkBorder: 'rgba(255,255,255,0.12)',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            backdropBlur: {
                glass: '16px',
            },
            boxShadow: {
                glass: '0 8px 32px rgba(31, 41, 55, 0.12)',
                'glass-lg': '0 16px 48px rgba(31, 41, 55, 0.18)',
                'glass-dark': '0 8px 32px rgba(0, 0, 0, 0.4)',
                'glass-dark-lg': '0 16px 48px rgba(0, 0, 0, 0.5)',
            },
            borderRadius: {
                'glass': '1rem',    // 16px
                'glass-lg': '1.5rem', // 24px
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-in-out',
                'slide-up': 'slideUp 0.4s ease-out',
                'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(16px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                pulseSoft: {
                    '0%, 100%': { opacity: '1' },
                    '50%': { opacity: '0.6' },
                },
            },
            transitionDuration: {
                400: '400ms',
            },
        },
    },
    plugins: [],
};
