# Spacing & Layout

Spacing uses a `rem`-based scale. Layout is tablet-first: the live roasting screen targets 1024×768 portrait or landscape iPad as its primary form factor.

## Spacing Scale

Spacing is exposed as CSS custom properties (`--space-*`) in [static/css/tokens.css](../../../static/css/tokens.css). The recurring rhythm is:

| Value | Usage |
|---|---|
| `0.25rem / 4px` | Icon-to-text gap inside a button |
| `0.5rem / 8px` | Tight gaps (icon buttons, inside stepper) |
| `0.75rem / 12px` | Stepper internal gap, chart-section padding |
| `1rem / 16px` | Default gap between siblings, form-row gap, button gap |
| `1.25rem / 20px` | Card grid gap, live-panel gap |
| `1.5rem / 24px` | Nav item padding, card padding, section spacing |
| `1.75rem / 28px` | Setup-section padding, timer/data-entry padding |
| `2rem / 32px` | Form padding, detail-section bottom padding, container padding |

## Radii

| Value | Usage |
|---|---|
| `4px` | Small UI (calc-display, review cards, log item) |
| `6px` | Buttons, form inputs, dropdown items |
| `8px` | Cards, panels, setup section, roast detail |

## Touch Targets

Tablet-first interaction rules:

- **Minimum 44px** height for any interactive control (stepper, form input in live-roast rows).
- **54px+** preferred for primary touch targets during a live roast.
- **88px** top-bar height on the live screen (`.live-topbar`) — values must be readable from ~60 cm.
- **Steppers** (`.stepper-control`) use a fixed 44px height with 0.75rem internal gap and 6px padding for the +/- tap area.

## Containers

| Container | Max width | Notes |
|---|---|---|
| `.nav-container` | `1600px` | Navbar inner wrapper |
| `.container` | `1600px`, `2rem 1.5rem` padding | Main content wrapper on most pages |
| `.live-roast-container` | `100%` | Live screen takes full viewport width — no horizontal max |

## Grids

Common grid patterns found in the codebase:

- **Cards grid** (`.beans-grid`, `.roasts-list`): `repeat(auto-fill, minmax(300px, 1fr))` + `1.25rem` gap.
- **Form row** (`.form-row`): `1fr 1fr` + `var(--space-4)` gap, collapsed to one column below 768px.
- **Detail grid** (`.detail-grid`): fixed `repeat(2, 1fr)` with `0.75rem 2rem` gaps.
- **Compact event buttons** (`.event-buttons-compact`): fixed `repeat(5, 1fr)` — one row across the live controls bar.

## Breakpoints

RoastLogger uses a small, pragmatic set of media queries. Keep new CSS aligned with these thresholds rather than inventing new ones.

| Query | Intent |
|---|---|
| `@media (max-width: 768px)` | Mobile — stack card grids into one column, collapse navbar, shrink modals |
| `@media (min-width: 769px) and (max-width: 1024px)` | Tablet-specific tuning |
| `@media (min-width: 768px)` | Fullscreen mode: larger instrument font sizes |
| `@media (min-width: 1024px)` | Fullscreen mode: wider left panel |
| `@media (hover: none) and (pointer: coarse)` | Touch-only devices — remove hover states, enlarge tap targets |
| `@media print` | Print styles (reviews, roast detail) |

Safe-area insets (`env(safe-area-inset-*)`) are applied on fullscreen panels for notched devices.

## Card & Shadow Pattern

Cards and panels share a consistent recipe:

```css
background: var(--card-bg);
border-radius: 8px;
box-shadow: var(--shadow);
padding: 1.75rem; /* or 1.5rem for smaller cards */
```

On hover (when applicable):

```css
box-shadow: var(--shadow-hover);
transform: translateY(-2px);
```

See [../components/cards-surfaces.md](../components/cards-surfaces.md) for the full component.
