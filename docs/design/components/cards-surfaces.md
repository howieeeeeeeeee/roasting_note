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
| `.form-section` | Full-page edit form panels (add/edit bean, roast edit) | `var(--space-7)` |
| `.roast-detail` | Detail page container | `2rem` |
| `.modal-content` | Modal body | variable (see form/modal patterns) |
| `.surface-flat` | Static management section | `var(--manage-section-padding)` |
| `.flat-section-group` | Several related static sections in one shell | One shared border with sparse internal dividers |
| `.settings-sheet` | Viewport-bounded Settings surface | section-specific |

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

Dialogs and menus may use `--shadow-modal` or `--shadow-lg` because elevation
communicates that they sit above the current workspace. Static management
sections use `.surface-flat` or `.flat-section-group` with no shadow. This
keeps form and detail pages from reading as a stack of nested cards.

## Borders vs Shadows

RoastLogger prefers quiet elevation with a border and low shadow for durable work surfaces. Borders are used for:

- Internal dividers (card header → body → footer: `1px solid var(--border-color)`).
- Form inputs (`1px solid var(--border-color)`, shifts to `--primary-color` on focus).
- Instrument panels sitting *inside* a card, where a subtle border helps them read as distinct sub-surfaces.

Full-page forms should not put a card around other cards. The `.form` wrapper only constrains width; each `.form-section` is the visible surface.

## Settings Side Sheet

Settings is the one modal surface that uses a viewport edge as structural
hierarchy. `.settings-sheet-overlay` aligns `.settings-sheet` to the right.
The sheet is no wider than `560px`, fills `100dvh`, and uses a left border plus
the modal shadow instead of a floating card margin. Below `768px`, it becomes a
full-screen surface with no radius or side border.

The title and section navigation occupy fixed grid rows. Only
`.settings-sheet-body` scrolls, with contained overscroll, so the page and
overlay remain stationary. Internal groups use one divider between related
topics rather than nested cards.

## Flat Management Surfaces

Management pages add `.surface-flat` to form and detail sections where a
shadow does not communicate hierarchy. The section keeps the shared surface,
border, radius, and semantic tokens but removes elevation and uses
`--manage-section-padding`.

Tables do not use `.surface-flat` because their existing containers already
own the surface and border. `.management-table-container` only removes the
shadow and preserves internal horizontal scrolling. This is especially
important for the fixed-width Beans columns and the RN-0027 Stock meter.

Compact detail screens use a 12-column outer grid from `1024px` and one column
below that threshold. Sections remain separate semantic regions; only their
placement, gap, and padding change.

## Dark Mode

Card surfaces (`.card-bg`) are `#171512` in dark mode — slightly lighter than the page background (`#0E0D0B`). The 7-step delta between them is enough to separate a card from the page without needing a border. Shadows become deeper (`rgba(0,0,0,0.4)`) so cards still visually float.

Explicit dark-mode overrides exist for `.setup-section`, `.timer-section`, `.data-entry-section`, `.timeline-section`, `.right-panel`, `.live-topbar`, `.live-controls-bar`, and `.bottom-controls` because they were authored before the palette was fully tokenised. New surfaces should just consume `var(--card-bg)` and need no override.

## Review Cards (`.review-card`)

Compact review cards use the same neutral surface recipe as other dense cards:

```css
background: var(--surf2);
border: 1px solid var(--bd2);
padding: var(--space-4);
border-radius: var(--radius-md);
```

No left accent strip. Reviews are often scanned in a grid, and the colored strip adds visual noise without adding information.

Empty review sections keep the same `.detail-section` shell but use `.review-section-footer` for a compact Add Review action. Do not use a full-width primary button in an empty review panel; it creates a heavy bar that competes with roast data.

Review card hover uses a neutral grey contour (`--txt3`) rather than the primary accent. Hover should only clarify the target area.
