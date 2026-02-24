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
Click **Auto-fill from Bean** to populate fields from existing bean data. Roast level remains empty (no source field on bean). Roast date defaults to today.

### Templates
Three built-in templates:
- **Minimal** — centered text, white background, Inter font, thin separator
- **Classic** — left-aligned, Roboto Slab font, accent bar using bean color
- **Compact** — smaller dimensions, two-column label+value layout

### Template Customization
Expand **Customize Template** to adjust per-field:
- Font family (Inter, Roboto Slab, Arial, Georgia, Courier New, Times New Roman)
- Font size
- X/Y position
- Text color

Click **Reset to Default** to clear all customizations.

### Save & Download
- **Save Label Info** — persists label fields (name, origin, process, roast level, flavor notes, roast date), template selection, image choice, export dimensions, and accent color to `beans.label`
- **Download PNG** — exports the label as a 2x retina PNG file (`{bean_name}_label.png`)

## API

`POST /api/beans/<bean_id>/label` — save label data (JSON body).

## Data Model

Label data stored as optional `label` dict on the bean document. See `docs/architecture/data-models.md`.
