/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "rgb(var(--color-background) / <alpha-value>)",
        surface1: "rgb(var(--color-surface-1) / <alpha-value>)",
        surface2: "rgb(var(--color-surface-2) / <alpha-value>)",
        surface3: "rgb(var(--color-surface-3) / <alpha-value>)",
        primary: "rgb(var(--color-primary) / <alpha-value>)",
        "primary-light": "rgb(var(--color-primary-light) / <alpha-value>)",
        "primary-dark": "rgb(var(--color-primary-dark) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        success: "rgb(var(--color-success) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        "on-background": "rgb(var(--color-on-background) / <alpha-value>)",
        "on-surface": "rgb(var(--color-on-surface) / <alpha-value>)",
        "on-surface-muted": "rgb(var(--color-on-surface-muted) / <alpha-value>)",
        "on-surface-disabled": "rgb(var(--color-on-surface-disabled) / <alpha-value>)",
        outline: "rgb(var(--color-outline) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["Inter", "Roboto", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1rem",
      },
      boxShadow: {
        glow: "0 0 24px rgb(var(--color-primary) / 0.18)",
        panel: "0 18px 48px rgb(0 0 0 / 0.32)",
        elevated: "0 1px 0 rgb(255 255 255 / 0.04) inset, 0 18px 48px rgb(0 0 0 / 0.24)",
      },
    },
  },
  plugins: [],
};
