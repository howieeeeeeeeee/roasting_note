# Cards & Surfaces

The neutral container elements that hold content: bean cards, roast cards, form panels, detail panes, and the live-roast panels.

## Anatomy

Every card shares the same base recipe:

```css
background: var(--card-bg);
border-radius: 8px;
box-shadow: var(--shadow);
padding: 1.5rem to 2rem;
```

## Variants

| Class | Use | Padding |
|---|---|---|
| `.bean-card`, `.roast-card` | Grid cards on list pages | `1.5rem` header + body + footer segments |
| `.setup-section`, `.timer-section`, `.data-entry-section`, `.timeline-section` | Large panels on the live roast screen | `1.75rem` |
| `.chart-section`, `.log-section` | Chart + log panels | `1.5rem` – `1.75rem` |
| `.form` | Full-width forms (add/edit bean, roast edit) | `2rem` |
| `.roast-detail` | Detail page container | `2rem` |
| `.modal-content` | Modal body | variable (see form/modal patterns) |

## Grid Layout

Card lists use auto-filling grids so they reflow to the container width without media-query juggling:

```css
.beans-grid, .roasts-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.25rem;
}
```

- 300px is the minimum card width; cards only narrow once the viewport can't fit another column.
- Below `768px`, the media query collapses grids to a single column.

## Internal Structure (`.bean-card`, `.roast-card`)

```
┌────────────────────────────────┐
│ .bean-card-header  (padding 1.5rem, bottom border)
│   h3 (primary-color)
├────────────────────────────────┤
│ .bean-card-body    (padding 1.5rem, flex-grow)
│   <p>...</p>
├────────────────────────────────┤
│ .bean-card-footer  (padding 1rem 1.5rem, top border, flex gap 0.5rem)
│   [Edit]  [Delete]
└────────────────────────────────┘
```

`flex-direction: column` + `flex-grow: 1` on the body keeps footers aligned across cards of different content heights.

## Elevation

| State | Shadow |
|---|---|
| Idle | `var(--shadow)` — `0 1px 3px rgba(0,0,0,0.08)` (light) / `0 1px 4px rgba(0,0,0,0.4)` (dark) |
| Hover (list cards) | `var(--shadow-hover)` + `transform: translateY(-2px)` |

Hover lift is reserved for **clickable** cards (the whole card is a link). Static cards (form panels, chart containers) don't lift.

## Borders vs Shadows

RoastLogger prefers **shadow over border** for card elevation. Borders are used for:

- Internal dividers (card header → body → footer: `1px solid var(--border-color)`).
- Form inputs (`1px solid var(--border-color)`, shifts to `--primary-color` on focus).
- Instrument panels sitting *inside* a card, where a subtle border helps them read as distinct sub-surfaces.

## Dark Mode

Card surfaces (`.card-bg`) are `#171512` in dark mode — slightly lighter than the page background (`#0E0D0B`). The 7-step delta between them is enough to separate a card from the page without needing a border. Shadows become deeper (`rgba(0,0,0,0.4)`) so cards still visually float.

Explicit dark-mode overrides exist for `.setup-section`, `.timer-section`, `.data-entry-section`, `.timeline-section`, `.right-panel`, `.live-topbar`, `.live-controls-bar`, and `.bottom-controls` because they were authored before the palette was fully tokenised. New surfaces should just consume `var(--card-bg)` and need no override.

## Review Cards (`.review-card`)

Special variant — uses a coloured **left accent border** instead of the full card shadow:

```css
background: #f9f9f9;
border-left: 4px solid var(--primary-color);
padding: 1rem;
border-radius: 4px;
```

Smaller, flatter, denser — appropriate because reviews are read in lists of many.
