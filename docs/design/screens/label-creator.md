# Label Creator Screen — Design

**Opens as:** Modal on the bean detail page ([templates/beans_detail.html](../../../templates/beans_detail.html))
**Behaviour / API / data model:** [docs/features/bean-label-creator.md](../../features/bean-label-creator.md)
**Template system:** [../patterns/label-templates.md](../patterns/label-templates.md)

A modal-based canvas editor for designing printable PNG labels for roasted coffee beans.

## Access

Bean detail page → **Create Label** button in header actions → opens modal.

## Layout Regions

The modal is divided into three vertical columns on desktop:

```text
┌─────────────────────────────────────────────────────────────┐
│  Create Label                                          [×]  │  ← modal header
├──────────────────────────────────────────────────────────────
│  [Auto-fill from Bean]  [Save Label Info]                  │  ← action bar
├─────────────────────────────────┬───────────────────────────┤
│                                 │                           │
│  Name           | Origin        │                           │
│  Process        | Roast Level   │                           │
│  Flavor Notes (textarea, full)  │     Preview canvas        │
│  Roast Date     | Image         │     (live render)         │
│  Template | Font | Aspect Ratio │                           │
│  Export W | Export H | Export px│                           │
│                                 │                           │
├─────────────────────────────────┴───────────────────────────┤
│                                              [⬇PNG] [⟳PNG]  │
└─────────────────────────────────────────────────────────────┘
```

On narrow screens the modal stacks top-to-bottom: controls above, preview below, fields at the bottom.

## Interaction Model

1. **Pick a template** (Nova / Ink / Strip / Washi) — preview re-renders immediately.
2. **Pick a font preset** (Modern / Editorial / Technical / Bold / Craft) — preview re-renders.
3. **Pick an aspect ratio** (2:1, 5:3, 5:4, 4:3, 3:4) — canvas dimensions change, preview re-renders.
4. **Edit label fields** — each keystroke redraws the canvas.
5. **(Optional) Click "Auto-fill from Bean"** — pulls `name`, `origin`, `process`, and `short_flavor_notes` from the bean. The short flavor notes array is joined with newlines for the label's multi-line flavor notes field. Roast level stays empty; roast date defaults to today.
6. **(Optional) Tweak export size in cm** — live pixel-dimension readout sits beside the cm inputs.
7. **Save**, **Download PNG**, or **Download PNG (Rotated 90°)** — the rotated variant emits the same render rotated 90° clockwise for sideways-feeding label printers.

Every visual change is immediate. There is no "Apply" step — the preview is the source of truth, and saving serialises whatever state is on screen.

## Preview Canvas

- Rendered by [static/js/label-creator.js](../../../static/js/label-creator.js) (`LabelCreator.renderLabel`).
- Render scale: **4×** — a 500×400 design canvas is drawn at 2000×1600 and down-scaled for display. Export is at full render scale (hi-DPI).
- Fonts are guaranteed loaded before drawing via `document.fonts.ready` + explicit `document.fonts.load(weight + family)` per preset — without this, Canvas silently falls back to system sans-serif.
- Re-draws on every field / template / preset / ratio / image change. Cheap because the canvas is small.

## Accent Colour

Inherited from the bean's `color` field. Flows to:

- **Nova**: vertical accent strip (hidden when image fills the right half).
- **Ink**: top accent line.
- **Strip**: left vertical accent band with rotated origin text and process pill.
- **Washi**: corner dots.

Users can override the accent inside the modal — it only writes back to the bean if the user saves.

## Image Handling

- Picker is populated from `GET /api/label/images` (lists `/static/img/` contents).
- Per-template image behaviour:
  - **Nova**: fills the right half. Without an image, a warm gradient stands in. The left text content is biased slightly upward for better visual balance.
  - **Ink / Washi**: full-bleed background with a dark / warm overlay on top.
  - **Strip**: image is not used.

## Save vs Download

- **Save Label Info** → `POST /api/beans/<bean_id>/label`. Persists `templateId`, `fontPreset`, `aspectRatio`, `imageSrc`, `accentColor`, `exportWidthCm`, `exportHeightCm`, and all label fields to `beans.label`. Reopening the modal restores the last saved state.
- **Download PNG** → exports the current canvas at render scale as `{bean_name}_label.png`.
- **Download PNG (Rotated 90°)** → exports the same canvas rotated 90° clockwise as `{bean_name}_label_rot90.png`. Render scale is preserved; the on-screen preview is unaffected.

Both downloads embed a PNG `pHYs` chunk computed from the cm export size, so the image inserts at exactly the chosen physical size in Word and other apps that honour `pHYs`. The rotated variant declares swapped width / height (rotation transposes the printable dimensions).

These are independent: users can download without saving, and vice versa.

### Remembered style preferences

When opening the modal for a bean **with no saved label**, the template / font / aspect dropdowns are seeded from the most recently updated bean that does have a saved label, via `GET /api/label/preferences`. So a user who consistently picks Ink + Editorial for their roasts gets that as their starting point on every new bean — without any per-browser state. Beans with an existing saved label still load their own saved values. If no bean has a saved label yet, the hardcoded fallback (`nova` / `modern` / `5:4`) is used.

## Dark Mode

The modal chrome (form fields, buttons, background) adapts automatically via CSS variables. The preview canvas itself **does not invert** — a label design is a print artefact, not a UI surface. The canvas draws exactly what will be printed, regardless of UI theme.

## Related Docs

- [../patterns/label-templates.md](../patterns/label-templates.md) — the four templates, five font presets, five aspect ratios as a design system.
- [../../features/adding-label-templates.md](../../features/adding-label-templates.md) — how to add a new template (step-by-step).
