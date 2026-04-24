# Label Creator Screen — Design

**Opens as:** Modal on the bean detail page ([templates/beans_detail.html](../../../templates/beans_detail.html))
**Behaviour / API / data model:** [docs/features/bean-label-creator.md](../../features/bean-label-creator.md)
**Template system:** [../patterns/label-templates.md](../patterns/label-templates.md)

A modal-based canvas editor for designing printable PNG labels for roasted coffee beans.

## Access

Bean detail page → **Create Label** button in header actions → opens modal.

## Layout Regions

The modal is divided into three vertical columns on desktop:

```
┌─────────────────────────────────────────────────────────────┐
│  Create Label                                          [×]  │  ← modal header
├─────────────┬──────────────────────────┬────────────────────┤
│             │                          │                    │
│  Template   │                          │  Label Info        │
│  picker     │    Preview canvas        │  (name, origin,    │
│  (4 cards)  │    (live render)         │   process, …)      │
│             │                          │                    │
│  Font preset│                          │  Fonts / Ratio     │
│  (5 chips)  │                          │  Export size (cm)  │
│             │                          │                    │
│  Aspect     │                          │  Accent colour     │
│  ratio      │                          │  Image dropdown    │
│  (5 chips)  │                          │                    │
│             │                          │                    │
│             │                          │  [Save] [Download] │
└─────────────┴──────────────────────────┴────────────────────┘
```

On narrow screens the modal stacks top-to-bottom: controls above, preview below, fields at the bottom.

## Interaction Model

1. **Pick a template** (Nova / Ink / Strip / Washi) — preview re-renders immediately.
2. **Pick a font preset** (Modern / Editorial / Technical / Bold / Craft) — preview re-renders.
3. **Pick an aspect ratio** (2:1, 5:3, 5:4, 4:3, 3:4) — canvas dimensions change, preview re-renders.
4. **Edit label fields** — each keystroke redraws the canvas.
5. **(Optional) Click "Auto-fill from Bean"** — pulls `name`, `origin`, `process` from the bean. Leaves roast level / flavor notes empty. Roast date defaults to today.
6. **(Optional) Tweak export size in cm** — live pixel-dimension readout sits beside the cm inputs.
7. **Save** or **Download PNG**.

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
  - **Nova**: fills the right half. Without an image, a warm gradient stands in.
  - **Ink / Washi**: full-bleed background with a dark / warm overlay on top.
  - **Strip**: image is not used.

## Save vs Download

- **Save Label Info** → `POST /api/beans/<bean_id>/label`. Persists `templateId`, `fontPreset`, `aspectRatio`, `imageSrc`, `accentColor`, `exportWidthCm`, `exportHeightCm`, and all label fields to `beans.label`. Reopening the modal restores the last saved state.
- **Download PNG** → exports the current canvas at render scale as `{bean_name}_label.png`.

These are independent: users can download without saving, and vice versa.

## Dark Mode

The modal chrome (form fields, buttons, background) adapts automatically via CSS variables. The preview canvas itself **does not invert** — a label design is a print artefact, not a UI surface. The canvas draws exactly what will be printed, regardless of UI theme.

## Related Docs

- [../patterns/label-templates.md](../patterns/label-templates.md) — the four templates, five font presets, five aspect ratios as a design system.
- [../../features/adding-label-templates.md](../../features/adding-label-templates.md) — how to add a new template (step-by-step).
