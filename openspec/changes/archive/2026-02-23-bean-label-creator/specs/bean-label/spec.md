## ADDED Requirements

### Requirement: Open Label Creator Modal
The system SHALL provide a "Create Label" button on the bean detail page that opens a label creator modal.

#### Scenario: Open modal from bean detail
- **WHEN** user clicks the "Create Label" button on the bean detail page
- **THEN** a modal opens with label info fields, template selector, and a live canvas preview
- **AND** if `beans.label` data exists for this bean, the fields are pre-populated with saved values
- **AND** if no saved label data exists, all text fields are empty

#### Scenario: Close modal
- **WHEN** user clicks the close button or clicks outside the modal
- **THEN** the modal closes without saving

---

### Requirement: Auto-fill Label Fields
The system SHALL provide a one-click auto-fill button that populates label fields from existing bean data.

#### Scenario: Auto-fill from bean data
- **WHEN** user clicks the "Auto-fill from Bean" button
- **THEN** the `name` field is populated with `bean.name`
- **AND** the `origin` field is populated with `bean.origin`
- **AND** the `process` field is populated with `bean.process`
- **AND** the `roastLevel` field remains empty (no source field on bean)
- **AND** the `roastDate` field is populated with today's date
- **AND** the canvas preview updates immediately to reflect the new values

#### Scenario: Auto-fill overwrites current form values
- **WHEN** user has edited fields in the modal and clicks "Auto-fill from Bean"
- **THEN** all fields are overwritten with bean data (except roastLevel which clears)
- **AND** unsaved edits are replaced

---

### Requirement: Live Canvas Preview
The system SHALL render a real-time preview of the label on an HTML5 canvas element.

#### Scenario: Preview updates on field change
- **WHEN** user types in any label text field (name, origin, process, roastLevel, roastDate)
- **THEN** the canvas re-renders immediately showing the updated text

#### Scenario: Preview updates on template change
- **WHEN** user selects a different template from the template dropdown
- **THEN** the canvas re-renders with the new template layout, fonts, and dimensions

#### Scenario: Preview updates on customization change
- **WHEN** user modifies a template customization setting (font size, font family, position, color)
- **THEN** the canvas re-renders reflecting the customization

#### Scenario: Retina rendering
- **WHEN** the canvas is rendered
- **THEN** internal canvas resolution SHALL be 2x the display dimensions for sharp output

---

### Requirement: Template Selection
The system SHALL provide built-in label templates that users can choose from.

#### Scenario: List available templates
- **WHEN** the label modal is open
- **THEN** a template dropdown shows all built-in templates: "Minimal", "Classic", "Compact"
- **AND** "Minimal" is the default if no template was previously saved

#### Scenario: Select template
- **WHEN** user selects a template from the dropdown
- **THEN** the preview updates to show the selected template's layout
- **AND** any previous template customizations are cleared (reset to template defaults)

---

### Requirement: Template Customization
The system SHALL allow users to customize template settings per field.

#### Scenario: Expand customization panel
- **WHEN** user clicks "Customize Template" in the modal
- **THEN** a collapsible section expands showing per-field customization options

#### Scenario: Customize field font size
- **WHEN** user changes the font size for a specific field
- **THEN** the preview updates with the new font size for that field

#### Scenario: Customize field font family
- **WHEN** user selects a different font family for a field
- **THEN** the preview updates with the new font
- **AND** available fonts SHALL be limited to: Inter, Arial, Georgia, Courier New, Times New Roman

#### Scenario: Customize field position
- **WHEN** user changes the X or Y position values for a field
- **THEN** the field moves to the new position in the preview

#### Scenario: Customize field color
- **WHEN** user changes the color for a field
- **THEN** the preview updates with the new text color

#### Scenario: Reset customizations
- **WHEN** user clicks "Reset to Default"
- **THEN** all customizations are cleared and the template reverts to its default field settings

---

### Requirement: Save Label Info
The system SHALL allow users to persist label data to the bean document.

#### Scenario: Save label data
- **WHEN** user clicks "Save Label Info" in the modal
- **THEN** a POST request is sent to `/api/beans/<bean_id>/label` with the label fields, selected templateId, and any customFields
- **AND** `roastDate` is NOT included in the saved data
- **AND** a success indicator is shown to the user

#### Scenario: Reload saved label data
- **WHEN** user opens the label modal for a bean that has saved label data
- **THEN** text fields are populated from `beans.label` (name, origin, process, roastLevel)
- **AND** the saved template is selected
- **AND** saved customizations are applied to the preview
- **AND** roastDate field is empty (not persisted)

---

### Requirement: Download Label as PNG
The system SHALL allow users to export the label as a PNG image file.

#### Scenario: Download PNG
- **WHEN** user clicks the "Download PNG" button
- **THEN** a PNG file is downloaded to the user's device
- **AND** the filename follows the pattern `{bean_name}_label.png` with spaces replaced by underscores
- **AND** the PNG resolution is 2x the template dimensions (retina quality)

#### Scenario: Download without saving
- **WHEN** user modifies fields and clicks "Download PNG" without clicking "Save Label Info"
- **THEN** the PNG is generated from the current canvas state
- **AND** the label data is NOT automatically saved to the database
