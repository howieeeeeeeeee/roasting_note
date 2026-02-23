## ADDED Requirements

### Requirement: Log Key Timing Event
The user can record discrete named milestones at specific points in the roast.

#### Scenario: Log key event
- **WHEN** POST `/api/roast/add_timing/<roast_id>` is called with `event_name`, `time_seconds`, `temperature`, `fan_setting`, `power_setting`
- **THEN** the event is appended to the roast's `key_timings` array
- **AND** RoR is calculated and stored if temperature data is available

#### Scenario: Reject invalid time
- **WHEN** `time_seconds` is negative or greater than 7200
- **THEN** a 400 response is returned
- **AND** no event is recorded

#### Scenario: Fan/power carry-forward
- **WHEN** `fan_setting` or `power_setting` are not provided in the request
- **THEN** the values are carried forward from the most recent `temp_curve` entry (defaults: fan=9, power=3)

---

### Requirement: Log Temperature Curve Entry
The system records a continuous stream of temperature + settings data during a roast.

#### Scenario: Log temp curve entry
- **WHEN** POST `/api/roast/add_event/<roast_id>` is called with `time_seconds`, `temperature`, `fan_setting`, `power_setting`, and optional `note` (singular)
- **THEN** the entry is appended to the roast's `temp_curve` array
- **AND** RoR is calculated and stored if temperature data is available

#### Scenario: Reject invalid time
- **WHEN** `time_seconds` is negative or greater than 7200
- **THEN** a 400 response is returned

---

### Requirement: Drop Event on Roast End
A "Drop" milestone is automatically appended when the roast ends.

#### Scenario: Drop event logged
- **WHEN** the roast is ended via POST `/api/roast/end/<roast_id>`
- **THEN** a key timing entry with `event_name: "Drop"` is appended to `key_timings`
- **AND** the current temperature is recorded if available

---

### Requirement: Manual Custom Events
During live roasting, users can log freeform custom events with optional notes.

#### Scenario: Log custom event
- **WHEN** a user enters a custom event name and optional note and submits it
- **THEN** the event is appended to `key_timings` with the current elapsed time and sensor data

---

### Requirement: Time After First Crack
The system tracks elapsed time from First Crack to Drop for roast development analysis.

#### Scenario: Time after FC calculated
- **WHEN** viewing a completed roast that has both a "First Crack Start" event and a "Drop" event
- **THEN** `time_after_first_crack_seconds` is calculated as `drop_time - first_crack_start_time`
- **AND** displayed on the dashboard and roast detail view
