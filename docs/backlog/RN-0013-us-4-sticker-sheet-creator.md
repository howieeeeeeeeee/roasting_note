---
id: RN-0013
title: US-4 Sticker Sheet Creator for Bean Labels
type: feature
status: pending
priority: medium
created: 2026-05-01
resolved:
area: label-creator
tags:
  - labels
  - stickers
  - printing
  - pdf
---

# US-4 Sticker Sheet Creator for Bean Labels

## Description

Add a sticker-sheet creation flow from the bean detail page. The flow lets a user pick the US-4 sheet template, select one or more images from their local disk, choose how many sticker slots each image should occupy, position the crop for each slot, and download a US Letter-sized PDF with four 4" × 5" stickers placed exactly on the template.

This is separate from the current single-label PNG export: the output is a full-sheet print artefact that places selected images into fixed physical slots. Everything stays in the browser — no upload, no persistence.

## Details

### Entry point

- Add a **Create Stickers** action on the bean detail page near the existing **Create Label** button in the header actions.
- The action opens a new modal (separate from the existing label modal) so the single-label flow is never disturbed.

### Template

- Initial release ships **US-4 only**. The UI must still expose a template selector (preselected to US-4, disabled or single-option) so adding more templates later is purely additive.
- US-4 spec:
  - Sheet size: **8.5" × 11"** (US Letter)
  - Sticker size: **4" × 5"** (portrait)
  - Top / bottom margin: **0.5"**
  - Left / right margin: **0.17"**
  - Horizontal spacing: **0.16"**
  - Vertical spacing: **0"**
  - Layout: 2 columns × 2 rows, four sticker slots total.
- US-4 slot origins, in inches from the top-left of the sheet:
  - Top-left: `x=0.17`, `y=0.5`
  - Top-right: `x=4.33`, `y=0.5`
  - Bottom-left: `x=0.17`, `y=5.5`
  - Bottom-right: `x=4.33`, `y=5.5`

### Image selection

- Use a native browser file picker (`<input type="file" accept="image/*" multiple>`). Images are read in-browser only — never uploaded, never saved to the bean. Closing the modal discards them.
- Each picked image is shown as a thumbnail with: filename, a per-image quantity input, and a remove button.
- For each image, the user sets how many sticker slots it should fill. The total across all images must equal exactly **4** before export is enabled. Validation message appears when the total ≠ 4.
- Supported quantity patterns include `4`, `2 + 2`, `1 + 3`, `1 + 1 + 1 + 1`, and any combination summing to 4.

### Slot placement

- Slots are filled in row-major order (top-left → top-right → bottom-left → bottom-right) automatically. No manual per-slot assignment in v1.
- When the same image fills multiple slots, each slot renders the image identically (same crop, same orientation).

### Image fit and orientation

- Default fit mode is **cover / crop** — the image fills the entire 4" × 5" slot edge-to-edge with no blank bands.
- **Auto-rotate to fit:** if the source image's orientation doesn't match the portrait slot, it is rotated 90° before cropping so it fills the slot naturally. This matches the existing rotated-PNG export behaviour. Most existing bean labels are landscape (5×4), so this auto-rotation is the common path.
- **Draggable crop position:** in the live preview, the user can drag the image within its slot to choose what gets centered. Crop position is per-image and applies uniformly to every slot using that image.
- No "contain" fallback in v1 — cover/crop is the only fit mode.

### Preview

- The modal shows a **live full-sheet preview** sized proportionally to US Letter, with all four slots visible and the current crop applied. The preview is the source of truth for what the PDF will contain.
- The preview updates immediately on image add, quantity change, drag-to-crop, or remove.
- No crop marks, slot outlines, or guides on the exported PDF. The preview may show faint slot outlines for editing only — the export must not.

### Export

- Single download action: **Download PDF**.
- Output is a single-page US Letter PDF (8.5" × 11"). Each image is placed at its slot's exact physical coordinates so the sheet prints at 100% scale and aligns with US-4 sticker stock.
- Generated entirely client-side using **jsPDF** (new static dependency loaded via `static/js/`). No new backend endpoint, no upload.
- Filename: `{bean_name}_us4_stickers.pdf`.
- Embedded images should be downscaled appropriately for print (~300 DPI at 4×5 in ≈ 1200×1500 px) so the PDF stays a reasonable size.

### Non-regression

- The existing **Create Label** modal, saved label data, single PNG export (standard and rotated 90°), and `GET /api/label/preferences` flow must continue to work unchanged.

## Acceptance Criteria

- [ ] Bean detail page has a **Create Stickers** action next to **Create Label** in the header.
- [ ] Clicking it opens a new modal independent of the existing label modal.
- [ ] Template selector shows **US-4** preselected (disabled / single-option for now).
- [ ] User can select one or more images via the native file picker (`accept="image/*"`, `multiple`). Files are read in-browser only — never uploaded, never persisted.
- [ ] Each selected image shows a thumbnail, a quantity input, and a remove control.
- [ ] UI validates that per-image quantities sum to exactly 4. Export is disabled with a clear message when the sum is not 4.
- [ ] Slots are filled row-major (top-left → top-right → bottom-left → bottom-right).
- [ ] Each image is auto-rotated to portrait if source orientation is landscape, then center-cropped to fill its 4" × 5" slot edge-to-edge (cover/crop, no blank bands).
- [ ] User can drag an image within its slot in the preview to adjust the crop position; the same crop applies to every slot using that image.
- [ ] A live full-sheet preview renders all four slots accurately; updates immediately on image add, quantity change, drag, or remove.
- [ ] **Download PDF** generates a single-page US Letter PDF named `{bean_name}_us4_stickers.pdf` using jsPDF, client-side only.
- [ ] PDF prints at 100% scale and aligns with US-4 sticker paper. Slots are positioned at the exact inch coordinates listed in Details.
- [ ] No crop marks, slot outlines, or guides appear in the exported PDF.
- [ ] Existing Create Label modal, saved label data, single PNG export (standard + rotated), and `/api/label/preferences` continue to work unchanged.
- [ ] Docs updated when implemented:
  - `docs/features/sticker-sheet.md` — new feature doc covering behaviour, template spec, jsPDF approach, no-persistence note (link from `docs/features/bean-label-creator.md` and `docs/features/README.md`).
  - `docs/design/screens/sticker-sheet.md` — new screen doc for the modal layout, slot preview, drag-to-crop interaction (link from `docs/design/screens/README.md` if present, plus `docs/README.md` navigation).
  - `docs/design/patterns/sticker-templates.md` — new pattern doc for the US-4 template (sheet size, slot grid, margins, spacing) so additional templates can follow the same structure.
  - `docs/architecture/tech-stack.md` — add jsPDF as a new client-side dependency.
  - `docs/README.md` — top-level navigation entries for the new feature/design/pattern docs.

## Open Questions

- Should the **Create Stickers** entry be a second top-level header button, or grouped under a new dropdown/menu alongside **Create Label** to keep the header tidy as more print actions are added? no it should be at the ppage where we see all the beans
- For users who pick the same image to fill all 4 slots, should drag-to-crop apply identically to all 4 slots (current spec) or be adjustable per slot (more powerful, more UI)? yes, adjust per slot
- Maximum number of selectable images and per-image file size limit (to avoid sluggish in-browser PDF generation)? Suggested default: max 4 images, max 10 MB each — confirm or tighten. yes, do what you say
- When the user re-opens **Create Stickers** for the same bean within the same browser session, should the previous selection persist in memory, or always start empty? (Cross-session persistence is already ruled out.) yes, you can use the one in memory
- Should the export support a "draft" mode that overlays slot outlines for proofing before printing on real sticker stock, distinct from the final clean export? no
- Any accessibility requirements for the drag-to-crop interaction (keyboard nudge, reset button per image)? good to have those.

## Related Files

- `templates/beans_detail.html`
- `static/js/label-creator.js`
- `static/js/` — new sticker-sheet module to be added
- `docs/features/bean-label-creator.md`
- `docs/features/sticker-sheet.md` — new doc
- `docs/design/screens/label-creator.md`
- `docs/design/screens/sticker-sheet.md` — new doc
- `docs/design/patterns/label-templates.md`
- `docs/design/patterns/sticker-templates.md` — new doc
- `docs/architecture/tech-stack.md`
