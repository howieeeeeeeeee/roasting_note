## Context

The app is a Flask + Jinja2 server-rendered app with vanilla JS. Bean detail page (`beans_detail.html`) already has a modal pattern (reviews modal) using `.modal` / `.modal-content` CSS classes with `display: block/none` toggling. Beans are stored in MongoDB with fields like `name`, `origin`, `process`. No image generation exists yet — Chart.js is used for roast curves but no canvas-to-PNG export.

The label creator needs to fit into this existing vanilla JS + Jinja2 architecture. No frontend framework or build step is available.

## Goals / Non-Goals

**Goals:**
- Let users create and download PNG labels from the bean detail page
- Persist label field overrides to `beans.label` so they're remembered
- One-click auto-fill from existing bean data
- Provide 2-3 built-in templates with a live canvas preview
- Allow template customization (font, size, positioning)
- Keep it zero-dependency (HTML5 Canvas only)

**Non-Goals:**
- Custom image/logo upload on labels (future)
- Batch label generation across multiple beans
- Print-directly-from-browser functionality
- QR codes or barcodes on labels
- Multi-language label support

## Decisions

### 1. Canvas-based rendering (not DOM-to-image)

**Choice:** Use HTML5 Canvas API directly to draw label content and export via `canvas.toDataURL('image/png')`.

**Why not DOM-to-image (html2canvas)?** Adds a dependency, inconsistent cross-browser rendering, and harder to control pixel-perfect output. Canvas gives direct control over font rendering, positioning, and export quality with zero dependencies.

### 2. Template data structure

**Choice:** Templates are plain JS objects defining dimensions, background, and an array of field slots.

```js
{
  id: "minimal",
  name: "Minimal",
  width: 400,
  height: 250,
  backgroundColor: "#FFFFFF",
  padding: 20,
  fields: [
    { key: "name",       x: 200, y: 40,  fontSize: 24, fontFamily: "Inter", fontWeight: "bold",   align: "center", color: "#333" },
    { key: "origin",     x: 200, y: 75,  fontSize: 14, fontFamily: "Inter", fontWeight: "normal", align: "center", color: "#666" },
    { key: "process",    x: 200, y: 100, fontSize: 12, fontFamily: "Inter", fontWeight: "normal", align: "center", color: "#888" },
    { key: "roastLevel", x: 200, y: 135, fontSize: 14, fontFamily: "Inter", fontWeight: "bold",   align: "center", color: "#6B5B4D" },
    { key: "roastDate",  x: 200, y: 220, fontSize: 11, fontFamily: "Inter", fontWeight: "normal", align: "center", color: "#999" }
  ],
  decorations: [
    { type: "line", x1: 40, y1: 155, x2: 360, y2: 155, color: "#DDD", width: 1 }
  ]
}
```

**Why this shape?** Each field has its own position, font, and alignment — this gives full per-field customization. The `decorations` array allows simple lines/shapes without overcomplicating the system. Users modify field properties directly when customizing.

**Alternative considered:** CSS-based templates with DOM rendering — rejected because export to PNG would require html2canvas dependency.

### 3. Built-in templates

Ship with 3 templates:

| Template | Style | Dimensions | Notes |
|----------|-------|------------|-------|
| **Minimal** | Clean, centered text, thin separator line | 400×250 | Default. White background, Inter font |
| **Classic** | Left-aligned, bean color accent bar on left | 400×250 | Uses bean's color as accent |
| **Compact** | Smaller, 2-column layout (labels + values) | 350×200 | Dense info, good for small bags |

### 4. `beans.label` schema

**Choice:** Store as a flat dict on the bean document.

```json
{
  "label": {
    "name": "Ethiopia Yirgacheffe",
    "origin": "Ethiopia",
    "process": "Washed",
    "roastLevel": "Medium",
    "templateId": "minimal",
    "customFields": {
      "name": { "fontSize": 28 },
      "origin": { "color": "#444" }
    }
  }
}
```

- `name`, `origin`, `process`, `roastLevel` — text overrides for label (may differ from bean's actual fields)
- `templateId` — which template is selected
- `customFields` — per-field overrides to template defaults (only stores diffs, not full config)
- `roastDate` is NOT stored — it's a transient field entered at download time

**Why `customFields` as diffs?** Keeps the stored data small. When rendering, merge template defaults with customFields overrides. If user hasn't customized anything, `customFields` is `{}`.

### 5. Auto-fill behavior

**Choice:** A single "Auto-fill from bean" button that populates all text fields at once from existing bean data.

Mapping:
- `name` ← `bean.name`
- `origin` ← `bean.origin`
- `process` ← `bean.process`
- `roastLevel` ← empty (no existing field on bean — user fills manually)
- `roastDate` ← today's date (pre-filled as convenience, editable)

If `beans.label` already has saved values, auto-fill overwrites them in the form (but doesn't save until user clicks Save). This is the "one-time fill in" feature.

### 6. Modal layout

The modal is wider than existing modals to accommodate the live preview canvas alongside the form controls. Layout:

```
┌─────────────────────────────────────────────────┐
│  Create Label                              [×]  │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Auto-fill from Bean]                          │
│                                                 │
│  ┌─ Label Info ──────┐  ┌─ Preview ──────────┐  │
│  │ Name: [________]  │  │                    │  │
│  │ Origin: [______]  │  │   ┌────────────┐   │  │
│  │ Process: [_____]  │  │   │            │   │  │
│  │ Roast Lvl: [___]  │  │   │  (canvas)  │   │  │
│  │ Roast Date: [__]  │  │   │            │   │  │
│  │                   │  │   └────────────┘   │  │
│  │ Template: [▾ sel] │  │                    │  │
│  └───────────────────┘  └────────────────────┘  │
│                                                 │
│  ▸ Customize Template (collapsible)             │
│    Font Family: [▾]  Font Size: [▾ per field]   │
│    Position X/Y: [__] [__]  Color: [picker]     │
│                                                 │
│  [Save Label Info]  [Download PNG]              │
│                                                 │
└─────────────────────────────────────────────────┘
```

- Left panel: form fields + template selector
- Right panel: live canvas preview (re-renders on any field/template change)
- Bottom: collapsible customization section (advanced, hidden by default)
- Two action buttons: Save (persists to DB) and Download (exports PNG)

On mobile: stacks vertically (form above, preview below).

### 7. API design

Single endpoint for saving label data:

```
POST /api/beans/<bean_id>/label
Content-Type: application/json

{
  "name": "Ethiopia Yirgacheffe",
  "origin": "Ethiopia",
  "process": "Washed",
  "roastLevel": "Medium",
  "templateId": "minimal",
  "customFields": {}
}
```

Response: `{ "success": true }`

This simply does `$set: { "label": <payload>, "updated_at": now }` on the bean document. No validation beyond basic type checking — label fields are free-form strings.

### 8. PNG export

```js
function downloadLabel(canvas, beanName) {
  const link = document.createElement('a');
  link.download = `${beanName.replace(/\s+/g, '_')}_label.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
}
```

Filename format: `{bean_name}_label.png` (spaces replaced with underscores).

### 9. File organization

All label JS code goes in a single new file `static/js/label-creator.js`:
- Template definitions (the 3 built-in templates)
- Canvas rendering function
- Modal open/close/auto-fill logic
- Download function
- Template customization handlers

This keeps label logic isolated from the rest of the app. The script tag is added only to `beans_detail.html`.

## Risks / Trade-offs

- **Font availability** → Canvas `fillText` uses system fonts. Inter is loaded via Google Fonts already, so the primary font is safe. If a user picks a font not loaded, canvas silently falls back to sans-serif. Mitigation: limit font picker to a curated list of web-safe fonts + Inter.
- **Canvas resolution on retina** → Default canvas renders at 1x, looking blurry on retina displays. Mitigation: render at 2x scale internally (`canvas.width = template.width * 2`, scale context by 2, set CSS size to template dimensions). Export will be 2x resolution which is good for printing.
- **No undo for template customization** → If a user changes field positions and saves, there's no "reset to default." Mitigation: add a "Reset to Default" button that clears `customFields` and restores the template's original settings.
- **Large modal on mobile** → The side-by-side layout won't fit on small screens. Mitigation: CSS media query to stack form above preview below 768px.
