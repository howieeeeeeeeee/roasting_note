# Roast Detail Screen — Design

**Template:** [templates/roast_detail.html](../../../templates/roast_detail.html)
**Behaviour:** Read-only view of a completed roast, with edit/archive/delete actions and reviews.

Short anatomy doc — no new design decisions. Built from standard [cards](../components/cards-surfaces.md), [forms](../components/forms.md), and [instrument displays](../components/instrument-displays.md).

## Layout

```
┌────────────────────────────────────────────────────────────┐
│  [Bean color dot] H1 Bean name                    ⋮  Back  │  ← .page-header + dropdown
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
| Page header | `.page-header`, `.header-actions`, `.dropdown-menu-container` | `style.css` – Page Header, Dropdown Menu sections |
| Container | `.roast-detail` | `style.css` – Detail Pages |
| Sections | `.detail-section` (bottom border, last-of-type removes it) | `style.css` – Detail Pages |
| Fact grid | `.detail-grid` + `.detail-item` | `style.css` – Detail Pages |
| Chart | `.chart-section` + shared [static/js/roast-chart.js](../../../static/js/roast-chart.js) | |
| Events | `.timeline` / combined events table | `style.css` – Timeline / Combined Events Table |
| Notes | `.notes-content` (white-space: pre-wrap) | `style.css` – Detail Pages |
| Reviews | `.review-card` list | [../components/cards-surfaces.md](../components/cards-surfaces.md#review-cards-review-card) |

## Interaction Notes

- Page header **right cluster** follows the standard pattern: one primary action (`Edit`) + a `⋮` dropdown menu holding destructive actions (Archive, Delete) + `Back` secondary button on the far right.
- Clicking a row in the events table does not edit — the screen is read-only. Editing happens via the `Edit` CTA which routes to the roast edit form.
- The chart reuses the live-roast `getChartColors()` dark-mode handling — same look in both contexts.

## Dark Mode

Inherits automatically; no custom rules needed.
