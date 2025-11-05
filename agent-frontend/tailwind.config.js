/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "primary": "#2b9dee",
        "background-light": "#f6f7f8",
        "background-dark": "#101a22",
        "sky-light": "#E0F2FE", // Lighter sky blue
        "sky-dark": "#B9E4FA",  // Darker sky blue
      },
      fontFamily: {
        "display": ["Noto Sans KR", "Inter"]
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
    },
  },
  plugins: [],
}
