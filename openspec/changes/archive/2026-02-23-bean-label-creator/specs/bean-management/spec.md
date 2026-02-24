## ADDED Requirements

### Requirement: Bean Label Data Storage
The bean document SHALL support an optional `label` dictionary field for storing label creator data.

#### Scenario: Bean without label data
- **WHEN** a bean document has no `label` field
- **THEN** the bean functions normally with no impact on existing behavior
- **AND** the label modal opens with empty fields

#### Scenario: Save label data via API
- **WHEN** a POST request is made to `/api/beans/<bean_id>/label` with a JSON body containing `name`, `origin`, `process`, `roastLevel`, `flavorNotes`, `roastDate`, `templateId`, `imageSrc`, `accentColor`, `exportWidthCm`, `exportHeightCm`, and optionally `customFields`
- **THEN** the bean document's `label` field is set to the provided dictionary
- **AND** `updated_at` is refreshed
- **AND** a JSON response `{ "success": true }` is returned

#### Scenario: Save label data with empty customFields
- **WHEN** label data is saved with `customFields` as an empty object `{}`
- **THEN** the label is stored with no template overrides

#### Scenario: Invalid bean ID
- **WHEN** a POST request is made to `/api/beans/<bean_id>/label` with a non-existent or archived bean ID
- **THEN** a 404 response is returned

#### Scenario: Label field schema
- **WHEN** label data is stored
- **THEN** the `label` field SHALL contain:
  - `name` (string): display name for the label
  - `origin` (string): origin text
  - `process` (string): process method text
  - `roastLevel` (string): roast level text
  - `flavorNotes` (string): flavor notes text
  - `roastDate` (string): roast date (YYYY-MM-DD)
  - `templateId` (string): ID of the selected template
  - `imageSrc` (string): path to selected image or empty for none
  - `accentColor` (string): hex color for accent bar
  - `exportWidthCm` (number): export width in cm
  - `exportHeightCm` (number): export height in cm
  - `customFields` (dict): per-field overrides keyed by field name, each containing optional `fontSize`, `fontFamily`, `color`, `x`, `y` properties
