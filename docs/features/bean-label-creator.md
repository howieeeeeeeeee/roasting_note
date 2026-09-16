# Bean Label Creator

Create and download printable PNG labels for roasted coffee beans.

> **Design spec** — layout, templates, fonts, aspect ratios, and the accent-colour system
> are documented under design docs:
>
> - [docs/design/screens/label-creator.md](../design/screens/label-creator.md) — modal screen anatomy
> - [docs/design/patterns/label-templates.md](../design/patterns/label-templates.md) — 4 templates × 5 font presets × 5 ratios as a design system
>
> Sticker sheet PDF output is a separate flow documented in [sticker-sheet.md](./sticker-sheet.md).

## Access

Bean detail page → **Create Label** button in header actions.

The **Create Stickers** action lives on the beans list page and opens a separate sticker-sheet PDF flow. It does not share this modal's saved label state.

## Label Fields

| Field | Description |
|---|---|
| `name` | Display name on label |
| `origin` | Country / region |
| `process` | Processing method |
| `roastLevel` | e.g. Light, Medium, Dark |
| `flavorNotes` | e.g. Berry, Spices, Cooked Peach |
| `roastDate` | Date of roast (defaults to today when empty) |

### Auto-fill

**Auto-fill from Bean** populates `name`, `origin`, `process`, and `flavorNotes` from the current bean. Bean `short_flavor_notes` is stored as an array and joined with newlines for the label field, so notes such as `Blueberry`, `Jasmine`, and `Dark Chocolate` render as separate lines. If the bean has no short flavor notes, `flavorNotes` remains blank. Roast level remains empty, and roast date defaults to today.

## Behaviour

- **Template / font preset / aspect ratio pickers** — live re-render on selection.
- **Image picker** — populated from `GET /api/label/images` (lists `/static/img/`).
- **Export size** — set in cm. The `5:4` default is `12.7 × 10.16` (4×5 in), and changing aspect ratio reseeds export width/height to a matching default pair. Effective pixel size shown live beside the inputs (reflects `RENDER_SCALE` from the renderer).
- **Exact physical size on print.** The exported PNG embeds a `pHYs` chunk encoding the chosen cm dimensions as pixels-per-meter. Word, Pages, LibreOffice, and most browsers honour `pHYs` and place the image at exactly that size when
 inserted — so a 12.7 × 10.16 cm label dropped into a Word doc prints at exactly 12.7 × 10.16 cm without any per-import scaling. PNGs without `pHYs` would default to 96 DPI and import enormous.
- **Save** and **Download** are independent — users can download without saving.
- **Style preferences are remembered.** When opening the label modal for a bean with no saved label, the template / font / aspect ratio dropdowns are seeded from the most recently updated bean that does have a saved label (via `GET /api/label/preferences`). Saved per-bean values still take precedence when re-opening an existing label. Falls back to `nova` / `modern` / `5:4` if no bean has a saved label yet.
- **Download PNG** comes in two variants: standard and **rotated 90°** (clockwise). The rotated export shares the same render scale and template; only the output orientation differs. Filename suffix is `_label.png` for standard and `_label_rot90.png` for rotated.

## API

- `POST /api/beans/<bean_id>/label` — save label data (JSON body).
- `GET  /api/label/images` — list available image assets under `/static/img/`.

## Data Model

Label data is stored as an optional `label` dict on the bean document. Saved keys:

```text
templateId, fontPreset, aspectRatio, imageSrc, accentColor,
exportWidthCm, exportHeightCm,
name, origin, process, roastLevel, flavorNotes, roastDate
```

See [docs/architecture/data-models.md](../architecture/data-models.md).

## Implementation

- **Renderer:** [static/js/label-creator.js](../../static/js/label-creator.js) — IIFE exposing `LabelCreator.renderLabel`, `loadImage`, presets, ratios. Defers drawing until `document.fonts.ready` resolves.
- **Modal markup and wiring:** [templates/beans_detail.html](../../templates/beans_detail.html).
- **Fonts:** Inter, Raleway, and DM Mono load globally from
  [templates/base.html](../../templates/base.html). Playfair Display, Barlow
  Condensed, and Roboto Slab are scoped to
  [templates/beans_detail.html](../../templates/beans_detail.html), the only
  route that opens the label creator. Both requests include every weight used
  by the canvas renderer before `document.fonts.ready` resolves.
- **Adding a new template:** [adding-label-templates.md](./adding-label-templates.md).

### Optional text sizing

Each label value has its own aligned 70–130% slider in the Text size panel.
The live percentage readout and canvas update together. Leaving a slider at
100% uses the template default; saving stores only changed values, and returning
it to 100% removes that field’s override. Reopening restores saved sizes. It is
per bean and does not seed other beans. The preview and both PNG exports use the
same sized canvas. Large text can exceed the available layout; use the preview
to choose a suitable size.

Database impact: only the optional beans.label.fontSizePercents field changes; no migration or backfill is needed locally or online. Normal timestamp-based document sync carries the field. No applied mirror is part of delivery. Read-only local-to-online preflight on 2026-09-16 succeeded (1 bean update forecast, no conflicts); no database was changed by preflight.
