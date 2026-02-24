
### Requirement: Create Bean
A user can create a green coffee bean record with purchase details.

#### Scenario: Create bean with full details
- **WHEN** a POST request is made to `/api/beans/add` with name, origin, process, supplier, purchase_date, purchase_price_total, purchase_weight_grams, stock_grams, notes, and color
- **THEN** a new bean document is saved with all provided fields
- **AND** `unit_price_per_kg` is calculated as `(purchase_price_total / purchase_weight_grams) * 1000`
- **AND** `created_at` and `updated_at` timestamps are set

#### Scenario: Create bean with minimal fields
- **WHEN** a POST request is made with only required fields
- **THEN** optional fields default to empty string or null

---

### Requirement: List Beans
Users can retrieve their bean inventory with filtering and sorting.

#### Scenario: List active beans (default)
- **WHEN** GET `/beans` is loaded with no filters
- **THEN** only non-archived beans with `stock_grams > 0` are shown
- **AND** results are sorted by name ascending

#### Scenario: Include out-of-stock beans
- **WHEN** the out-of-stock filter is enabled on the beans list page
- **THEN** non-archived beans with any stock level are shown

#### Scenario: Sort beans
- **WHEN** a sort option is selected on the beans list page
- **THEN** beans are re-sorted accordingly (by name, unit price, purchase date, or stock)

---

### Requirement: Get Single Bean
A user can retrieve the full details of one bean.

#### Scenario: Fetch existing bean
- **WHEN** GET `/beans/detail/<bean_id>` is loaded with a valid ID
- **THEN** the full bean document is displayed

#### Scenario: Fetch non-existent bean
- **WHEN** GET `/beans/detail/<bean_id>` is called with an invalid ID
- **THEN** a 404 response is returned

---

### Requirement: Update Bean
A user can edit any field of an existing bean.

#### Scenario: Update bean fields
- **WHEN** a POST request is made to `/api/beans/edit/<bean_id>` with changed fields
- **THEN** the bean document is updated with the new values
- **AND** `unit_price_per_kg` is recalculated if `purchase_price_total` or `purchase_weight_grams` changed
- **AND** `updated_at` is refreshed

---

### Requirement: Archive Bean
A user can soft-delete a bean so it no longer appears in active lists.

#### Scenario: Archive bean
- **WHEN** POST `/api/beans/delete/<bean_id>` is called
- **THEN** the bean's `archived` flag is set to `true`
- **AND** the bean no longer appears in default list responses
- **AND** the bean document is preserved in the database

---

### Requirement: Automatic Stock Tracking
Bean stock is automatically decremented and restored as roasts are created, edited, or archived.

#### Scenario: Decrement stock on roast creation
- **WHEN** a new roast is saved with a `bean_id` and `original_weight_grams`
- **THEN** the bean's `stock_grams` is decremented by `original_weight_grams`

#### Scenario: Restore stock on roast archival
- **WHEN** a roast is archived
- **THEN** the bean's `stock_grams` is restored by `original_weight_grams`

#### Scenario: Adjust stock on roast weight edit
- **WHEN** a roast's `original_weight_grams` is changed
- **THEN** the bean stock is adjusted by the delta `(new_weight - old_weight)`

#### Scenario: Adjust stock on bean reassignment
- **WHEN** a roast's `bean_id` is changed to a different bean
- **THEN** the old bean's stock is restored and the new bean's stock is decremented

---

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
