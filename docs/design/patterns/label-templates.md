# Label Templates — Design System

The printable bean labels aren't a single layout with variants — they are four independent visual systems sharing a common set of fields, font presets, aspect ratios, and an accent colour. This page documents the *what and why*. For the step-by-step on adding a new template, see [../../features/adding-label-templates.md](../../features/adding-label-templates.md).

**Renderer:** [static/js/label-creator.js](../../../static/js/label-creator.js)
**Screen:** [../screens/label-creator.md](../screens/label-creator.md)
**Feature spec:** [../../features/bean-label-creator.md](../../features/bean-label-creator.md)

## Four Templates

Each template has a distinct mood and information hierarchy. They are not alternative skins of the same design — switching template changes what is where.

| Template | Mood | Layout |
|---|---|---|
| **Nova** | Clean, modern, product-catalogue | Split layout: text left, image or warm gradient right, thin vertical accent strip between. The left text stack is intentionally shifted slightly upward to keep stronger top balance and avoid a bottom-heavy feel. |
| **Ink** | Confident, moody, premium | Dark full-bleed background, warm glow, subtle grain, top accent line; optional image darkened and used as background |
| **Strip** | Swiss-minimal, editorial | Off-white, coloured left accent band with rotated origin label and a process pill, restrained typography |
| **Washi** | Craft, handmade, artisan | Craft-paper gradient background, double ornamental border, centred typography with a diamond divider |

### Template Metadata

From [label-creator.js](../../../static/js/label-creator.js) `TEMPLATES`:

```js
nova:  { defaultRatio: '5:4', exportWidthCm: 5, exportHeightCm: 4 }
ink:   { defaultRatio: '5:4', exportWidthCm: 5, exportHeightCm: 4 }
strip: { defaultRatio: '5:4', exportWidthCm: 5, exportHeightCm: 4 }
washi: { defaultRatio: '5:4', exportWidthCm: 5, exportHeightCm: 4 }
```

All four default to the same aspect ratio and export size so switching template doesn't change the physical print dimensions unless the user explicitly changes them.

## Five Font Presets

Presets combine a bean-name face with a body face:

| Preset | Name font | Body font | Feel |
|---|---|---|---|
| **Modern** | Raleway 800 | Inter 400 | Geometric, confident |
| **Editorial** | Playfair Display 700 | Inter 400 | Magazine / serif authority |
| **Technical** | DM Mono 500 | DM Mono 400 | Instrument-panel, data-like |
| **Bold** | Barlow Condensed 800 | Inter 400 | Strong, industrial |
| **Craft** | Roboto Slab 700 | Roboto Slab 400 | Single-family, warm slab |

Presets are orthogonal to templates — any preset pairs with any template. The renderer applies the preset's face + weight to the name field and the body face to everything else.

See [../foundations/typography.md](../foundations/typography.md) for how fonts are loaded and the `document.fonts.ready` guard that prevents silent fallback.

## Five Aspect Ratios

From `ASPECT_RATIOS`:

- `2:1` — wide banner
- `5:3` — landscape
- `5:4` — default, slightly landscape
- `4:3` — squarer landscape
- `3:4` — portrait

Changing the ratio resizes the design canvas; `exportWidthCm` / `exportHeightCm` recalculate so the physical print stays near 5×4 cm or whatever the user has set.

## Fields

All four templates read from the same six field keys. A template chooses which to display and how to arrange them:

| Key | Purpose |
|---|---|
| `name` | Bean / coffee name (hero) |
| `origin` | Country or region |
| `process` | Processing method (Washed, Natural, Honey, …) |
| `roastLevel` | Light / Medium / Dark |
| `flavorNotes` | Tasting notes |
| `roastDate` | Date of roast (defaults to today) |

This shared schema is why "Auto-fill from Bean" works across templates — it writes field values, not template-specific strings.

## Accent Colour

A single `accentColor` value (inherited from `bean.color`, overridable in the modal) drives the template-specific accent:

| Template | How the accent is used |
|---|---|
| Nova | Vertical accent strip (hidden when right-half image is set) |
| Ink | Top accent line |
| Strip | Left vertical band behind rotated origin text and the process pill |
| Washi | Corner dots |

The renderer **does not assume accessible contrast** between accent and background — it pairs the user's chosen colour with the template's own fixed background (light or dark) which already carries the contrast burden.

## Render Scale & Export

From the renderer:

- **`RENDER_SCALE = 4`** — every design dimension is multiplied by 4 at render and export time.
- Design canvas at the preview is 500 × 400 at `5:4` but draws at 2000 × 1600 internally. Pixel dimensions are independent of the chosen cm size.
- Export PNG is the full-scale canvas → hi-DPI print, roughly 1000+ DPI at 5×4 cm.

## Persistence

When the user clicks **Save Label Info**, the renderer state is serialised to `beans.label`:

```
{
  templateId, fontPreset, aspectRatio, imageSrc,
  accentColor, exportWidthCm, exportHeightCm,
  name, origin, process, roastLevel, flavorNotes, roastDate
}
```

Reopening the modal restores this state verbatim. No migration logic — if a template ID or font preset stops existing, the user just picks a new one.

## Adding a New Template

See [../../features/adding-label-templates.md](../../features/adding-label-templates.md) for the step-by-step — template object schema, field positioning (`xPct` / `yPct`), decorations, accent-bar options, image placement, and a worked example.
