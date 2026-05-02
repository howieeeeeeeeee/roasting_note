# Bean Inventory Screens — Design

Two related screens: the beans list (`/beans`) and the bean detail page (`/beans/<id>`).

Short anatomy doc — no new design decisions. Built from standard [cards](../components/cards-surfaces.md), [tables](#table-style-on-beans-list), and [forms](../components/forms.md).

## Beans List

**Template:** [templates/beans_list.html](../../../templates/beans_list.html)

Table-style inventory view (not a card grid — density matters when managing dozens of beans).

```text
┌───────────────────────────────────────────────────────────────┐
│  Beans      [Filter] [Create Stickers] [+ Add New Bean]        │  ← .page-header
├───────────────────────────────────────────────────────────────┤
│  .beans-table                                                 │
│  ┌─────┬────────────────┬────────┬────────┬────────┬───────┐ │
│  │  ●  │ Name           │ Stock  │ Date   │ Price  │ … ⋮   │ │
│  ├─────┼────────────────┼────────┼────────┼────────┼───────┤ │
│  │  ●  │ Ethiopia Y.    │ 2.1 kg │ 04-02  │ €18.00 │       │ │
│  │     │ [Blueberry] [Jasmine] [Dark Chocolate]              │ │
│  └─────┴────────────────┴────────┴────────┴────────┴───────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Components Used

| Region | Class / component |
| --- | --- |
| Page header | `.page-header` + `.header-actions` |
| Filter panel | `.btn-filter` (toggles out-of-stock visibility) |
| Create Stickers | `.btn.btn-primary` with a Material icon — opens the [sticker sheet modal](./sticker-sheet.md) |
| Table | `.beans-table` (sortable via `.sort-btn-inline` + `.sortable-header`) |
| Row | `.bean-row.clickable-row` — whole row links to detail |
| Color cell | `.bean-name-cell` containing `.bean-color-indicator` (dot filled with `bean.color`) plus `.bean-short-flavor-preview` chips when `short_flavor_notes` exists |
| Actions | `.btn-icon` + `.dropdown-menu-container` in the last column |

The bean **color indicator** (the dot next to each name) is the first use of the user-defined `bean.color` field — users pick a hex value that then flows through to the bean detail header and the label creator's accent colour.

Short flavor notes render as small rounded chips below the bean name. They are intentionally compact and use `short_flavor_notes` only; the longer `notes` field stays on the bean detail page.

## Bean Form

The add/edit bean form uses a chip editor for `short_flavor_notes`: typing a note and pressing Enter creates a removable tag, Backspace removes the last tag when the input is empty, and pasted newline/comma-separated notes are split into tags. The form still submits the notes as newline-separated text so the backend can normalize them into the stored array.

## Bean Detail

**Template:** [templates/beans_detail.html](../../../templates/beans_detail.html)

```text
┌────────────────────────────────────────────────────────────────┐
│  [●] Bean name           [🏷 Create Label] [Edit] [Archive] …  │  ← .page-header
├────────────────────────────────────────────────────────────────┤
│  .roast-detail (reused container)                              │
│  H2 Overview  — .detail-grid [Origin][Process][Supplier][Date] │
│  H2 Short Flavor Notes — compact chips                         │
│  H2 Stock     — current stock, history, purchase log           │
│  H2 Roasts    — list of roasts made with this bean             │
│  H2 Notes     — .notes-content                                 │
└────────────────────────────────────────────────────────────────┘
```

### Detail Components

| Region | Class / component |
| --- | --- |
| Container | `.roast-detail` (reused from roast detail — same padding/shadow) |
| Color dot in header | `.bean-color-indicator` with inline `background-color: bean.color` |
| Sections | `.detail-section` + `.detail-grid` |
| Create Label | `.btn.btn-primary` with a Material icon — opens the [label creator modal](./label-creator.md) |

## Dark Mode

Both screens inherit automatically. The table's hover row (`.data-table tr:hover`) uses `#f5f5f5` in light mode; a dark-mode rule in [style.css](../../../static/css/style.css) swaps this for a subtle overlay.

## Table style on beans list

The beans list uses a custom `.beans-table` rather than the generic `.data-table`. Both share the same header/body/hover pattern but `.beans-table` adds:

- Fixed-width action column (`.actions-column`, 120px).
- Clickable rows (`.clickable-row` — cursor pointer, row background shift on hover).
- Inline sort buttons in the header (`.sort-btn-inline` with a toggling Material icon for asc/desc/unfold).
