# Bean Label Creator

Create and download printable PNG labels for roasted coffee beans.

> **Design spec** — layout, templates, fonts, aspect ratios, and the accent-colour system
> are documented under design docs:
>
> - [docs/design/screens/label-creator.md](../design/screens/label-creator.md) — modal screen anatomy
> - [docs/design/patterns/label-templates.md](../design/patterns/label-templates.md) — 4 templates × 5 font presets × 5 ratios as a design system

## Access

Bean detail page → **Create Label** button in header actions.

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

**Auto-fill from Bean** populates `name`, `origin`, and `process` from the current bean. Roast level and flavor notes remain empty (no source fields on bean). Roast date defaults to today.

## Behaviour

- **Template / font preset / aspect ratio pickers** — live re-render on selection.
- **Image picker** — populated from `GET /api/label/images` (lists `/static/img/`).
- **Export size** — set in cm (default 10 × 8). Effective pixel size shown live beside the inputs (reflects `RENDER_SCALE` from the renderer).
- **Save** and **Download** are independent — users can download without saving.

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
- **Fonts:** Raleway, Playfair Display, Barlow Condensed, Inter, Roboto Slab, DM Mono loaded in [templates/base.html](../../templates/base.html).
- **Adding a new template:** [adding-label-templates.md](./adding-label-templates.md).
