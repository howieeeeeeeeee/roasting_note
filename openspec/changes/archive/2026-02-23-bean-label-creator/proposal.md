## Why

There's no way to create printable labels for roasted coffee beans. After roasting, users need to label bags with bean info (name, origin, process, roast level, roast date) but currently do this manually. A label creator modal on the bean detail page would let users generate and download PNG labels directly from the app, using data already stored in the system.

## What Changes

- Add a "Create Label" button on the bean detail page (next to Edit/Archive)
- New modal with:
  - **Label info fields**: name, origin, process, roast level, roast date
  - **"Auto-fill" button**: one-click populate fields from existing bean data (roast date excluded from auto-fill since it's per-session)
  - **Save label info**: persist editable label fields to `beans.label` (dict) so they're remembered across sessions (roast date not saved — it's transient)
  - **Template selector**: choose from built-in label templates
  - **Template customization**: adjust font family, font size, element positioning, layout
  - **Live preview**: canvas-based preview of the label
  - **Download button**: export label as PNG
- New `beans.label` field on the bean document to store saved label metadata
- API endpoint to update `beans.label`

### Template System

Templates define the visual layout of a label:
- **Dimensions**: width × height in pixels (e.g., 400×250 for a standard bag label)
- **Font**: family, size per field, color
- **Layout**: position (x, y) and alignment of each text field
- **Background**: solid color or minimal decorative elements
- **Fields shown**: which fields to display and in what order

Ship with 2-3 built-in templates (e.g., "Minimal", "Classic", "Compact"). Users can customize font/size/position on any template. Custom template configs are saved to `beans.label.template` so the user's preferred layout is remembered per bean.

## Capabilities

### New Capabilities
- `bean-label`: Label creation modal with field editing, template selection, canvas preview, and PNG download. Includes persisting label data to the bean document and template customization.

### Modified Capabilities
- `bean-management`: Add `label` dict field to bean schema; add API endpoint for updating label data.

## Impact

- **Frontend**: New modal in `beans_detail.html`, new JavaScript for canvas rendering and PNG export (using HTML5 Canvas API — no new dependencies needed)
- **Backend**: New API route `POST /api/beans/<id>/label` to save label data; update bean edit logic to handle `label` field
- **Database**: New optional `label` field (dict) on beans collection — no migration needed, backward compatible
- **Dependencies**: None — uses native Canvas API for rendering and `canvas.toBlob()` / `canvas.toDataURL()` for PNG export
