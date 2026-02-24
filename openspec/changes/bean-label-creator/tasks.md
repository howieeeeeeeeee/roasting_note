## 1. Backend — API & Data Model

- [x] 1.1 Add `POST /api/beans/<bean_id>/label` endpoint in `app.py` that accepts JSON body, validates bean exists and is not archived, sets `label` dict and `updated_at` on the bean document, returns `{ "success": true }` or 404
- [x] 1.2 Pass `bean.label` data (if present) to `beans_detail.html` template context so the modal can pre-populate saved values
- [x] 1.3 Update `docs/architecture/data-models.md` to document the new optional `label` field on beans collection
- [x] 1.4 Update `docs/architecture/api-endpoints.md` to document the new label endpoint

## 2. Frontend — Modal Structure

- [x] 2.1 Add "Create Label" button to bean detail page header actions (next to Edit/Archive buttons) in `beans_detail.html`
- [x] 2.2 Add label creator modal HTML to `beans_detail.html` with: header, auto-fill button, label info form fields (name, origin, process, roastLevel, roastDate), template dropdown, canvas preview container, collapsible customization panel, Save and Download buttons
- [x] 2.3 Add modal open/close JS: `openLabelModal()` / `closeLabelModal()` with outside-click-to-close, pre-populate fields from `bean.label` Jinja data on open
- [x] 2.4 Add label modal CSS to `static/css/style.css`: wider modal (max-width ~900px), two-column layout (form left, preview right), collapsible customization section, mobile stacking below 768px

## 3. Frontend — Template Definitions & Canvas Rendering

- [x] 3.1 Create `static/js/label-creator.js` with the 3 built-in template objects (Minimal, Classic, Compact) following the design doc's data structure (id, name, width, height, backgroundColor, padding, fields array, decorations array)
- [x] 3.2 Implement `renderLabel(canvas, template, fieldValues, customFields)` function: clear canvas, set 2x retina scale, draw background, apply per-field customizations (merge template defaults with customFields overrides), draw text with correct font/size/position/alignment/color, draw decorations (lines)
- [x] 3.3 Wire up live preview: attach `input` event listeners to all label text fields and template dropdown `change` listener to call `renderLabel()` on every change
- [x] 3.4 Add the `<script src="/static/js/label-creator.js">` tag to `beans_detail.html`

## 4. Frontend — Auto-fill, Save & Download

- [x] 4.1 Implement auto-fill button handler: populate form fields from bean data (name, origin, process from Jinja context), set roastDate to today (YYYY-MM-DD), clear roastLevel, trigger canvas re-render
- [x] 4.2 Implement save handler: collect form values + templateId + customFields, POST to `/api/beans/<bean_id>/label` as JSON (exclude roastDate), show success/error feedback
- [x] 4.3 Implement download handler: call `canvas.toDataURL('image/png')`, create temporary `<a>` element with download attribute `{bean_name}_label.png`, trigger click

## 5. Frontend — Template Customization

- [x] 5.1 Implement collapsible customization panel toggle (expand/collapse with arrow indicator)
- [x] 5.2 Build per-field customization UI: field selector dropdown, font family dropdown (Inter, Arial, Georgia, Courier New, Times New Roman), font size number input, X/Y position inputs, color picker
- [x] 5.3 Track customizations in a `customFields` JS object (diffs from template defaults), apply overrides in `renderLabel()`, wire input listeners to update customFields and re-render
- [x] 5.4 Implement "Reset to Default" button: clear `customFields` object, reset customization form inputs to template defaults, re-render canvas

## 6. Testing & Documentation

- [x] 6.1 Add backend test for `POST /api/beans/<bean_id>/label` endpoint: test save success, 404 for invalid bean, verify label field persisted
- [ ] 6.2 Manually verify: open modal, auto-fill, edit fields, switch templates, customize, save, reopen (fields restored), download PNG
- [x] 6.3 Update `docs/features/` with a `bean-label-creator.md` feature doc
