/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                dentist: {
                    light: '#F0F9FF',
                    blue: '#0EA5E9',
                    dark: '#0369A1',
                    turquoise: '#2DD4BF',
                    accent: '#0D9488',
                },
            },
        },
    },
    plugins: [],
}
