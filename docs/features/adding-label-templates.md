# Adding Label Templates

How to create new label templates for the bean label creator.

## Template Location

All templates are defined in `static/js/label-creator.js` inside the `templates` object.

## Template Structure

```js
templateId: {
    id: 'templateId',          // Unique kebab-case ID
    name: 'Display Name',      // Shown in the dropdown
    width: 500,                // Design width in pixels (preview size)
    height: 400,               // Design height in pixels (preview size)
    exportWidthCm: 5,          // Default export width in cm
    exportHeightCm: 4,         // Default export height in cm
    backgroundColor: '#FFFFFF', // Canvas background color

    // Optional: accent bar (vertical colored bar)
    accentBar: true,
    accentBarX: 14,            // X position
    accentBarY: 28,            // Y position
    accentBarWidth: 5,         // Bar width in pixels
    accentBarHeight: 0.6,      // Height as fraction of total height (0-1)

    // Optional: image (e.g. logo, illustration)
    image: {
        src: '/static/img/your-image.png',
        xPct: 0.55,           // X position as fraction of width
        yPct: 0,              // Y position as fraction of height
        widthPct: 0.45,       // Width as fraction of total width
        heightPct: 1.0        // Height as fraction of total height
    },

    // Optional: uppercase all text
    uppercase: true,

    // Fields (text elements on the label)
    fields: [ ... ],

    // Decorations (lines, shapes)
    decorations: [ ... ]
}
```

## Fields

Each field maps to a form input in the label modal. Available field keys:

| Key | Description |
|-----|-------------|
| `name` | Bean/coffee name |
| `origin` | Country/region |
| `process` | Processing method |
| `roastLevel` | Roast level |
| `flavorNotes` | Tasting/flavor notes |
| `roastDate` | Date of roast |

### Field Properties

```js
{
    key: 'name',              // Which field value to display
    xPct: 0.048,              // X position as fraction of width (preferred)
    yPct: 0.115,              // Y position as fraction of height (preferred)
    // OR use absolute pixel positions:
    // x: 24, y: 46,
    fontSize: 28,             // Font size in pixels
    fontFamily: 'Inter',      // Font family
    fontWeight: 'bold',       // 'normal' or 'bold'
    align: 'left',            // 'left', 'center', or 'right'
    color: '#2C2C2C',         // Text color (hex)

    // Optional
    prefix: 'Roasted on: ',  // Text prepended to value
    label: 'Origin'           // For key-value layout (label on left, value on right)
}
```

**Positioning**: Use `xPct`/`yPct` (0-1 fractions) for positions that scale when the export size changes. Use absolute `x`/`y` only for fixed layouts.

## Decorations

Lines and dividers between sections:

```js
{
    type: 'line',
    x1Pct: 0.545, y1Pct: 0.02,  // Start point (fraction)
    x2Pct: 0.545, y2Pct: 0.98,  // End point (fraction)
    // OR absolute pixels: x1, y1, x2, y2
    color: '#E0E0E0',
    width: 1                     // Line width
}
```

## Image

Images are drawn with cover-fit (fills the area, crops overflow, maintains aspect ratio). Place the image file in `static/img/`.

```js
image: {
    src: '/static/img/my-image.png',
    xPct: 0.55,     // Left edge at 55% of width
    yPct: 0,         // Top edge
    widthPct: 0.45,  // Takes up 45% of width
    heightPct: 1.0   // Full height
}
```

## Resolution & Export

- **Render scale**: 5x (defined as `RENDER_SCALE` in the JS)
- **Export pixels**: design dimensions × 5
- **Example**: 500×400 design → 2500×2000 export → ~1270 DPI at 5cm×4cm print
- Users can adjust export size (cm) in the modal. The canvas re-renders at the new aspect ratio.

## Step-by-step: Adding a New Template

1. **Add the template object** to `templates` in `static/js/label-creator.js`:

```js
myTemplate: {
    id: 'myTemplate',
    name: 'My Template',
    width: 500,
    height: 400,
    exportWidthCm: 5,
    exportHeightCm: 4,
    backgroundColor: '#FFFFFF',
    fields: [
        { key: 'name', xPct: 0.05, yPct: 0.12, fontSize: 24,
          fontFamily: 'Inter', fontWeight: 'bold', align: 'left', color: '#333' },
        // ... more fields
    ],
    decorations: []
}
```

2. **Add an `<option>`** to the template dropdown in `templates/beans_detail.html`:

```html
<option value="myTemplate">My Template</option>
```

3. **If using an image**, place it in `static/img/` and add the `image` property.

4. **Test** by opening the label modal on any bean detail page and selecting your template.

## Tips

- Use the **Customize Template** panel in the modal to live-tweak field positions, then copy the values into the template definition.
- Keep text within the left portion if using a right-side image (e.g. `xPct` < 0.5).
- The accent bar color is set by the user in the modal (defaults to the bean's color).
- `fontFamily` should be a web-safe font or one already loaded by the app (Inter and Roboto Slab are loaded via Google Fonts).
