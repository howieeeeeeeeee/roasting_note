# Roast Detail Screen — Design

**Template:** [templates/roast_detail.html](../../../templates/roast_detail.html)
**Behaviour:** Read-only view of a completed roast, with edit/archive/delete actions and reviews.

Short anatomy doc — no new design decisions. Built from standard [cards](../components/cards-surfaces.md), [forms](../components/forms.md), and [instrument displays](../components/instrument-displays.md).

## Layout

```
┌────────────────────────────────────────────────────────────┐
│  H1 Roast name                         [Edit] ⋮             │  ← .page-header + dropdown
├────────────────────────────────────────────────────────────┤
│  .roast-detail (card, padding 2rem)                        │
│                                                            │
│  H2 Overview                                               │
│  .detail-grid (2 cols, 0.75rem × 2rem gaps)                │
│    [Date] [Green weight] [Roasted weight] [Loss %]         │
│    [Level] [Ambient] [Duration] [First Crack]              │
│                                                            │
│  H2 Roast Curve                                            │
│  .chart-section — full-width chart ([Shared roast-chart.js])│
│                                                            │
│  H2 Events Timeline                                        │
│  .timeline / .events-table                                 │
│                                                            │
│  H2 Notes                                                  │
│  .notes-content (pre-wrap)                                 │
│                                                            │
│  H2 Reviews                                                │
│  .reviews-list of .review-card                             │
└────────────────────────────────────────────────────────────┘
```

## Components Used

| Region | Component | File |
|---|---|---|
| Page header | `.page-header`, `.record-title-heading`, `.header-actions`, `.dropdown-menu-container` | `components/cards.css`, `components/modals.css` |
| Container | `.roast-detail` | `style.css` – Detail Pages |
| Sections | `.detail-section` (bottom border, last-of-type removes it) | `style.css` – Detail Pages |
| Fact grid | `.detail-grid` + `.detail-item` | `style.css` – Detail Pages |
| Chart | `.chart-section` + shared [static/js/roast-chart.js](../../../static/js/roast-chart.js) | |
| Events | `.timeline` / combined events table | `style.css` – Timeline / Combined Events Table |
| Notes | `.notes-content` (white-space: pre-wrap) | `style.css` – Detail Pages |
| Reviews | `.review-card` list | [../components/cards-surfaces.md](../components/cards-surfaces.md#review-cards-review-card) |
| Roast table actions | `.row-action-buttons` inside `.roast-name-cell` | `components/tables.css` |

## Interaction Notes

- Page header **right cluster** follows the standard pattern: one visible edit action plus a `⋮` dropdown menu holding destructive actions.
- Roast list/history tables do not show an Actions column. Row-level buttons appear as a hover/focus overlay at the right edge of the row, and the hovered row uses `--surf2` so the icons remain visible.
- Date/time values in the roast list and detail fact grid show operator-local wall time using `TIMEZONE`. The UI does not label these as UTC because raw UTC clock faces are not shown.
- Clicking a row in the events table does not edit — the screen is read-only. Editing happens via the `Edit` CTA which routes to the roast edit form.
- The chart reuses the live-roast `getChartColors()` dark-mode handling — same look in both contexts.
- Empty review sections use a compact Add Review button in `.review-section-footer`, not a full-width bar.

## Roast Edit Form

**Template:** [templates/roast_edit.html](../../../templates/roast_edit.html)

The edit form uses the shared `.form` and `.form-section` recipe. The roast title field uses `.form-group-title` so it matches roast names in list rows and detail headers. Basic information, weights, notes, and read-only roast data stay in separate sections.

`.management-form--roast` keeps those sections and their source order while
using desktop width more efficiently. From `1024px`, Basic Information spans
the form and lays its fields out in three columns; Weights and Notes share the
next row; Roast Data remains full width. Save Changes stays before Cancel in a
safe-area-aware sticky action row. All grids collapse to one column below
`768px`, and the action row becomes static for print.

The detail page uses `.management-detail--roast`: Basic Information occupies
half of the first desktop row, while Weights and Roast Duration occupy one
quarter each. Reviews, Roast Data, and General Notes stay full width so review
content, the roast curve, event history, and notes retain their existing
behavior. The chart dimensions and shared chart rendering are unchanged.

## Dark Mode

Inherits automatically; no custom rules needed.
