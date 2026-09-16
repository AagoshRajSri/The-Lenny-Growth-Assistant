# Design

## User & problem
Growth PMs and operators at product-led companies need a fast, source-grounded research tool for Lenny's Podcast / Newsletter corpus — not a generic chatbot. They come in during focused work sessions: writing strategy docs, preparing for planning cycles, validating growth bets. They need answers they can trust and cite, delivered in an interface that feels like a professional productivity tool rather than a marketing demo.


## Design Tokens & System

### Palette Rationale

The color palette is anchored in deep-slate backgrounds and a steel-blue primary accent (`#4a9eff`). This deliberately rejects two common AI-tool anti-patterns: the warm-cream/terracotta palette that reads as consumer brand, and the neon terminal-green palette that reads as developer toy. Instead, the system draws from GitHub-dark and Linear's tonal approach — precision tooling for people who take their work seriously. The accent is chosen to be a single, unambiguous interactive signal; every other value is neutral and surfaces data rather than shouting at the user.

### Token Definitions

| Token | CSS Variable | Value | Role |
|---|---|---|---|
| `bg` | `--color-bg` | `#0d1117` | Page/viewport background |
| `surface` | `--color-surface` | `#161b22` | Cards, panels, sidebar |
| `surface-hover` | `--color-surface-hover` | `#1c2330` | Hover lift for list items |
| `surface-raised` | `--color-surface-raised` | `#1f2937` | Modals, popovers, code blocks |
| `border` | `--color-border` | `#30363d` | All dividers and edges |
| `border-focus` | `--color-border-focus` | `#4a9eff` | Keyboard-focus ring |
| `text-primary` | `--color-text-primary` | `#e6edf3` | All primary readable text |
| `text-muted` | `--color-text-muted` | `#8b949e` | Timestamps, metadata, labels |
| `text-disabled` | `--color-text-disabled` | `#484f58` | Placeholders, disabled states |
| `accent` | `--color-accent` | `#4a9eff` | Links, CTAs, interactive blue |
| `accent-hover` | `--color-accent-hover` | `#6ab0ff` | Accent hover/active boost |
| `accent-subtle` | `--color-accent-subtle` | `#1a3a5c` | Selected row backgrounds |
| `success` | `--color-success` | `#3fb950` | Positive state indicators |
| `warning` | `--color-warning` | `#d29922` | Warning / degraded indicators |
| `error` | `--color-error` | `#f85149` | Errors, destructive actions |

### Typography Rules

| Context | Font | Why |
|---|---|---|
| UI copy, chat messages, headings | `Inter` (sans-serif) | Maximum legibility for prose and labels |
| Code blocks, chunk IDs, model tags, source metadata | `JetBrains Mono` (monospace) | **Strictly reserved** for technical content — never used decoratively |

Monospace fonts are applied via three mechanisms: `<code>` / `<pre>` / `<kbd>` HTML elements, and explicit CSS class selectors `.chunk-id`, `.model-tag`, `.source-meta`. No other UI elements may use the mono font family.

### Spacing Scale

Based on a `0.25rem` (4px) base unit: `1 = 4px`, `2 = 8px`, `3 = 12px`, `4 = 16px`, `6 = 24px`, `8 = 32px`.

### Elevation

Shadows are intentionally minimal (black at 40–50% opacity). There are no colorful drop shadows or glows. Elevation is communicated through background-color layering: `bg → surface → surface-raised`.

### Accessibility

- **Contrast ratios**: `--color-text-primary` (`#e6edf3`) on `--color-bg` (`#0d1117`) achieves ≥ 12:1 (WCAG AAA). `--color-accent` (`#4a9eff`) on `--color-bg` achieves ≥ 4.7:1 (WCAG AA). All text-on-surface combinations are verified AA+.
- **Focus states**: `:focus-visible` is implemented globally via a 3px ring in `--color-accent` with 35% opacity. Mouse users see no visible ring (`:focus:not(:focus-visible)` suppresses it). This is WCAG 2.4.11 compliant.
- **Reduced motion**: An `@media (prefers-reduced-motion: reduce)` block at the root collapses all animation/transition durations to `0.01ms`, disabling visual motion for users who request it. This covers all CSS transitions system-wide without requiring per-component overrides.
- **Semantic HTML**: All interactive elements use `button`, `a`, or labeled `input` — no click-handlers on `div` elements.
