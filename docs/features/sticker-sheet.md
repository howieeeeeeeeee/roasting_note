# Sticker Sheet Creator

Create a print-ready US-4 sticker sheet PDF from local image files.

> **Design specs**
>
> - [docs/design/screens/sticker-sheet.md](../design/screens/sticker-sheet.md) - modal layout and sheet preview
> - [docs/design/patterns/sticker-templates.md](../design/patterns/sticker-templates.md) - US-4 physical template

## Access

Beans list page (`/beans`) -> **Create Stickers** button next to the out-of-stock filter.

## Behaviour

- **Separate modal.** The sticker sheet flow is independent from the bean label modal and does not affect saved label data.
- **Template selector.** The selector shows `US-4` preselected and disabled until more templates exist.
- **Local files only.** Images are selected with `<input type="file" accept="image/*" multiple>`, read with `FileReader`, and never uploaded or saved to the bean.
- **In-memory state.** Closing and reopening the modal in the same page session keeps selected images in memory. Reloading the page clears them.
- **Limits.** Up to 4 images can be selected, and each file must be 10 MB or smaller.
- **Quantities.** Each image has a quantity from 1 to 4. The UI warns when quantities do not total exactly 4, but export stays available as long as at least one image is selected. Totals below 4 leave trailing slots blank; totals above 4 export only the first 4 row-major slots.
- **Slot order.** Slots are filled row-major: top-left, top-right, bottom-left, bottom-right.
- **Auto-rotate.** Landscape sources are rotated 90 degrees in-browser before center-cover fitting into the portrait 4 in x 5 in slot.
- **Preview as source of truth.** The full US Letter preview shows all four slots with faint editing outlines. Export omits those outlines.

## Template

Initial release ships only **US-4**:

| Property | Value |
| --- | --- |
| Sheet | 8.5 in x 11 in |
| Sticker | 4 in x 5 in |
| Layout | 2 columns x 2 rows |
| Top / bottom margin | 0.5 in |
| Left / right margin | 0.17 in |
| Horizontal spacing | 0.16 in |
| Vertical spacing | 0 in |

Slot origins from the sheet's top-left corner:

| Slot | x | y |
| --- | --- | --- |
| Top-left | 0.17 in | 0.5 in |
| Top-right | 4.33 in | 0.5 in |
| Bottom-left | 0.17 in | 5.5 in |
| Bottom-right | 4.33 in | 5.5 in |

## Export

**Download PDF** creates a single-page US Letter PDF named `us4_stickers.pdf`.

The export is generated entirely client-side by [static/js/sticker-sheet.js](../../static/js/sticker-sheet.js) using the vendored jsPDF UMD build at [static/js/jspdf.umd.min.js](../../static/js/jspdf.umd.min.js). Each slot is rendered through an offscreen 1200 x 1500 canvas, matching roughly 300 DPI for a 4 in x 5 in sticker, then placed in the PDF at the exact US-4 inch coordinates.

No backend endpoint, database field, upload, or persisted sticker-sheet document exists.

## Non-Regression

The existing bean label creator continues to use [static/js/label-creator.js](../../static/js/label-creator.js), `POST /api/beans/<bean_id>/label`, `GET /api/label/preferences`, and the PNG / rotated PNG export path unchanged.
