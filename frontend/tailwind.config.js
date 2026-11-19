/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        wine: {
          DEFAULT: "#7C0E44",
          50: "#FAF0F4",
          100: "#F5E0EB",
          200: "#E8B8CE",
          500: "#7C0E44",
          600: "#6B0C3B",
          700: "#5A0A32",
          800: "#490829",
          900: "#380620",
        },
        berry: {
          DEFAULT: "#AA5E7A",
          100: "#F6E8ED",
          200: "#E5C2CF",
          500: "#AA5E7A",
          600: "#964E68",
        },
        blush: {
          DEFAULT: "#D49A9A",
          100: "#F9ECEC",
          200: "#F0D3D3",
          500: "#D49A9A",
          600: "#BD7F7F",
        },
        cream: {
          DEFAULT: "#F2DACE",
          50: "#FAF4F0",
          100: "#F7EAE3",
          200: "#F2DACE",
          300: "#E9C4B3",
        },
        canvas: "#FAF8F7",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "#7C0E44",
          foreground: "#ffffff",
        },
        secondary: {
          DEFAULT: "#AA5E7A",
          foreground: "#ffffff",
        },
        muted: {
          DEFAULT: "#F2DACE",
          foreground: "#6B5B63",
        },
        card: {
          DEFAULT: "#ffffff",
          foreground: "#22161C",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};
