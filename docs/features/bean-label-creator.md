# Bean Label Creator

Create and download printable PNG labels for roasted coffee beans.

## Access

Bean detail page → **Create Label** button in header actions.

## Features

### Label Info Fields

- **Name** — display name on label
- **Origin** — country/region
- **Process** — processing method
- **Roast Level** — e.g. Light, Medium, Dark
- **Flavor Notes** — e.g. Berry, Spices, Cooked Peach
- **Roast Date** — date of roast (defaults to today when empty)

### Auto-fill

Click **Auto-fill from Bean** to populate fields from existing bean data. Roast level and flavor notes remain empty (no source fields on bean). Roast date defaults to today.

### Templates

Four built-in templates, each drawn on a canvas with font-aware typography:

- **Nova** — split layout, text on the left, image or warm gradient on the right, thin vertical accent strip
- **Ink** — dark full-bleed background, warm glow, subtle grain, top accent line; optional image is darkened and used as the background
- **Strip** — Swiss-minimal off-white layout with a coloured left accent band containing a rotated origin label and a process pill
- **Washi** — craft paper gradient, double ornamental border, centred typography with a diamond divider

### Font Presets

Pick one of five curated type pairings for the bean name and body text:

| Preset      | Name font          | Body font    |
| ----------- | ------------------ | ------------ |
| Modern      | Raleway            | Inter        |
| Editorial   | Playfair Display   | Inter        |
| Technical   | DM Mono            | DM Mono      |
| Bold        | Barlow Condensed   | Inter        |
| Craft       | Roboto Slab        | Roboto Slab  |

Fonts are loaded from Google Fonts in `templates/base.html`. The renderer defers drawing until `document.fonts.ready` resolves so the custom faces never fall back to system sans-serif.

### Aspect Ratios

Five selectable ratios driving the canvas width/height: `2:1`, `5:3`, `5:4` (default), `4:3`, `3:4`.

### Accent Colour

Inherited from the bean's `color` field. Used for accent strips, origin text on dark templates, corner dots on Washi, and the top accent line on Ink.

### Image

Optional — choose from files in `/static/img/` via the Image dropdown (populated from `GET /api/label/images`).

- **Nova**: image fills the right half of the label. Without an image, a clean warm gradient is rendered instead.
- **Ink / Washi**: image is used as a full-bleed background with a dark or warm overlay on top of it.
- **Strip**: image is not used.

### Export Dimensions

Export **W** and **H** are set in centimetres (default 10 × 8). The effective export pixel size is shown live beside the inputs and reflects the canvas hi-dpi scale.

### Save & Download

- **Save Label Info** — persists label fields, `templateId`, `fontPreset`, `aspectRatio`, `imageSrc`, `accentColor`, and `exportWidthCm` / `exportHeightCm` to `beans.label`.
- **Download PNG** — exports the current preview canvas as a hi-dpi PNG (`{bean_name}_label.png`).

## API

- `POST /api/beans/<bean_id>/label` — save label data (JSON body).
- `GET  /api/label/images` — list available image assets under `/static/img/`.

## Data Model

Label data stored as optional `label` dict on the bean document. See `docs/architecture/data-models.md`.

## Implementation Notes

- Renderer: `static/js/label-creator.js` (IIFE exposing `LabelCreator.renderLabel`, `loadImage`, presets, ratios).
- UI / modal markup and wiring: `templates/beans_detail.html`.
- Required Google Fonts (Raleway, Playfair Display, Barlow Condensed, Inter, Roboto Slab, DM Mono) are loaded in `templates/base.html`.
