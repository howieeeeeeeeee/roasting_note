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

RoastLogger has two deliberate density contexts:

- **Browse and manage:** `--control-min: 44px` is the minimum target for navigation, forms, list actions, and Settings.
- **Live roasting:** `--control-live-min: 54px` protects primary roast controls and is never reduced by management density rules.
- **88px** top-bar height on the live screen (`.live-topbar`) — values must be readable from ~60 cm.
- **Steppers** (`.stepper-control`) use the protected 54px live target.

Management layouts use `--manage-gap`, `--manage-section-gap`, and
`--manage-section-padding`. The reusable `.manage-stack`, `.manage-grid`, and
`.surface-flat` hooks tighten vertical rhythm without shrinking controls.

## Containers

| Container | Max width | Notes |
|---|---|---|
| `.nav-container` | `1440px` | Navbar inner wrapper, fixed at 56px high |
| `.container` | `1440px`, token-based padding | Main content wrapper on most pages |
| `.live-roast-container` | `100%` | Live screen takes full viewport width — no horizontal max |
| `.settings-sheet` | `560px` desktop, `100%` mobile | Fixed right sheet with internal scrolling |

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

## Settings Viewport Contract

Settings uses `height: 100dvh` and three grid rows: title, section navigation,
and `minmax(0, 1fr)` content. Body scrolling is locked while it is open. Only
the content row has `overflow-y: auto` and `overscroll-behavior: contain`.

At heights up to `680px`, the title row and section padding tighten while
interactive controls remain at least `44px`. Below `768px` wide, the sheet is
full-screen and multi-action rows collapse to one column.

## Surface Pattern

Static management groups prefer a flat surface:

```css
background: var(--surf);
border: 1px solid var(--bd);
border-radius: var(--radius-xl);
box-shadow: none;
padding: var(--manage-section-padding);
```

Shadows and hover lift remain available when they communicate clickable or
overlay hierarchy. Do not nest elevated cards inside another elevated card.

See [../components/cards-surfaces.md](../components/cards-surfaces.md) for the full component.
