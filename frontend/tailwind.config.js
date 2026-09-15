/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Wire up CSS-variable tokens as Tailwind utility aliases
      // This lets us use e.g. `bg-surface`, `text-muted`, `border-border`
      // alongside arbitrary values without fighting the design system.
      colors: {
        bg:             "var(--color-bg)",
        surface:        "var(--color-surface)",
        "surface-hover":"var(--color-surface-hover)",
        "surface-raised":"var(--color-surface-raised)",
        border:         "var(--color-border)",
        "border-focus": "var(--color-border-focus)",
        primary:        "var(--color-text-primary)",
        muted:          "var(--color-text-muted)",
        disabled:       "var(--color-text-disabled)",
        accent:         "var(--color-accent)",
        "accent-hover": "var(--color-accent-hover)",
        "accent-subtle":"var(--color-accent-subtle)",
        success:        "var(--color-success)",
        warning:        "var(--color-warning)",
        error:          "var(--color-error)",
      },
      fontFamily: {
        sans:  ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        mono:  ["JetBrains Mono", "Fira Code", "ui-monospace", "Cascadia Code", "Roboto Mono", "monospace"],
      },
      fontSize: {
        xs:   ["var(--text-xs)",   { lineHeight: "1.4"  }],
        sm:   ["var(--text-sm)",   { lineHeight: "1.5"  }],
        base: ["var(--text-base)", { lineHeight: "1.6"  }],
        lg:   ["var(--text-lg)",   { lineHeight: "1.4"  }],
        xl:   ["var(--text-xl)",   { lineHeight: "1.3"  }],
        "2xl":["var(--text-2xl)",  { lineHeight: "1.25" }],
      },
      borderRadius: {
        sm:   "var(--radius-sm)",
        md:   "var(--radius-md)",
        lg:   "var(--radius-lg)",
        xl:   "var(--radius-xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm:    "var(--shadow-sm)",
        md:    "var(--shadow-md)",
        focus: "var(--shadow-focus)",
      },
      transitionDuration: {
        fast:   "var(--duration-fast)",
        normal: "var(--duration-normal)",
      },
    },
  },
  plugins: [],
}
