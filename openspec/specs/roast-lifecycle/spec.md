
### Requirement: Create Draft Roast
A new roast is initialized with sensible defaults so the user can immediately go to the live interface.

#### Scenario: Create roast with defaults
- **WHEN** POST `/api/roast/create` is called
- **THEN** a roast document is created with:
  - `title`: "Untitled Roast"
  - `roast_date`: today's date
  - `roaster`: "Freshroast SR800"
  - `temp_measurement_method`: "K-Type Sensor V1"
  - `archived`: false
- **AND** the response includes the new roast's `_id`

---

### Requirement: Update Roast Metadata
A user can edit roast fields — title, bean, weights, date, notes, method, and roaster.

#### Scenario: Update roast details
- **WHEN** POST `/api/roast/update/<roast_id>` is called with changed fields
- **THEN** the roast document is updated
- **AND** `updated_at` is refreshed

#### Scenario: Update calculates weight loss
- **WHEN** `original_weight_grams` and `roasted_weight_grams` are both present
- **THEN** `weight_loss_percentage` is calculated as `(original - roasted) / original * 100`

---

### Requirement: Start Roast Timer
Marking a roast as started sets the start time and locks certain fields.

#### Scenario: Start roast
- **WHEN** POST `/api/roast/start/<roast_id>` is called
- **THEN** `roast_start_time` is set to the current time with timezone
- **AND** bean stock is decremented by `original_weight_grams`

---

### Requirement: End Roast Timer
Marking a roast as ended records the finish time, logs a Drop event, and calculates duration.

#### Scenario: End roast
- **WHEN** POST `/api/roast/end/<roast_id>` is called
- **THEN** `roast_end_time` is set to the current time
- **AND** `roast_duration_seconds` is calculated as `end_time - start_time`
- **AND** a "Drop" event is appended to `key_timings`

---

### Requirement: Archive Roast
Roasts are soft-deleted so historical data is preserved.

#### Scenario: Archive roast
- **WHEN** POST `/api/roast/delete/<roast_id>` is called
- **THEN** the roast's `archived` flag is set to `true`
- **AND** the roast no longer appears in active list responses
- **AND** bean stock is restored by `original_weight_grams`

---

### Requirement: List Roasts
Users can browse their roast history in reverse chronological order.

#### Scenario: List all active roasts
- **WHEN** GET `/` (dashboard) is loaded
- **THEN** all non-archived roasts are displayed sorted by `roast_date` descending

#### Scenario: Dashboard shows roast metrics
- **WHEN** the dashboard is loaded
- **THEN** each roast shows duration, weight loss %, time after first crack, and review scores

---

### Requirement: Roast Detail View
A user can view the full details and history of a single completed roast.

#### Scenario: Fetch roast detail
- **WHEN** GET `/roast/detail/<roast_id>` is loaded
- **THEN** the full roast document is returned including temp_curve, key_timings, and reviews
