# Sticker Templates - Design Pattern

The sticker sheet template system documents fixed physical sheets used by [static/js/sticker-sheet.js](../../../static/js/sticker-sheet.js). Unlike bean label templates, sticker templates are about print geometry, not visual styling.

**Screen:** [../screens/sticker-sheet.md](../screens/sticker-sheet.md)
**Feature spec:** [../../features/sticker-sheet.md](../../features/sticker-sheet.md)

## Template Shape

Each template should define:

| Field | Purpose |
| --- | --- |
| `id` | Stable template key used by the UI |
| `name` | Human-readable selector label |
| `sheetWidthIn` / `sheetHeightIn` | Physical page size in inches |
| `slotWidthIn` / `slotHeightIn` | Physical sticker size in inches |
| `slots` | Ordered list of slot origins from the sheet top-left |

Slot order is semantic. The UI fills in array order and treats that order as row-major placement.

## US-4

Initial release ships `us4` only.

```js
{
  id: 'us4',
  sheetWidthIn: 8.5,
  sheetHeightIn: 11,
  slotWidthIn: 4,
  slotHeightIn: 5,
  slots: [
    { label: 'Top-left', x: 0.17, y: 0.5 },
    { label: 'Top-right', x: 4.33, y: 0.5 },
    { label: 'Bottom-left', x: 0.17, y: 5.5 },
    { label: 'Bottom-right', x: 4.33, y: 5.5 },
  ],
}
```

Derived margins and spacing:

| Measurement | Value |
| --- | --- |
| Top / bottom margin | 0.5 in |
| Left / right margin | 0.17 in |
| Horizontal spacing | 0.16 in |
| Vertical spacing | 0 in |
| Grid | 2 columns x 2 rows |

## Preview vs Export

The screen preview may add editing affordances, including dashed slot borders and slot numbers. Export code must render only the slot image canvases into the PDF so no guide marks print on sticker stock.

## Adding Templates Later

Additional templates should be additive:

1. Add a template object with exact inch dimensions.
2. Enable the template selector in the modal.
3. Keep slot filling deterministic by ordering slots row-major unless the stock requires another documented order.
4. Add a section to this pattern doc with physical measurements.
