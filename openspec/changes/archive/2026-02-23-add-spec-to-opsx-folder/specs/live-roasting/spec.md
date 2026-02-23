## ADDED Requirements

### Requirement: Live Roast Timer
The interface shows an elapsed timer that starts when the roast begins.

#### Scenario: Timer starts on roast start
- **WHEN** a user clicks "Start Roast"
- **THEN** `roast_start_time` is recorded in the database
- **AND** the UI timer begins counting up from 00:00

#### Scenario: Timer stops on roast end
- **WHEN** a user clicks "End Roast"
- **THEN** `roast_end_time` is recorded
- **AND** the timer stops and shows the final elapsed time

---

### Requirement: Real-Time Temperature and RoR Display
Temperature and RoR are polled from the sensor every second during an active roast.

#### Scenario: Per-second UI update
- **WHEN** the roast is active
- **THEN** every 1 second the UI calls `/api/temp/current_fast`
- **AND** the displayed temperature and RoR are updated

#### Scenario: Display when sensor offline
- **WHEN** the fast-read returns null temperature
- **THEN** the UI displays "Offline" for temperature
- **AND** RoR is not displayed or shows "--"

---

### Requirement: Fan and Power Controls
The user can adjust fan and power settings (1–9) during the roast.

#### Scenario: Adjust fan or power
- **WHEN** a user changes the fan or power slider
- **THEN** the new value is immediately reflected in the UI
- **AND** a `temp_curve` entry is logged with the updated setting

#### Scenario: Default fan and power
- **WHEN** a new roast is started
- **THEN** fan defaults to 9 and power defaults to 3

---

### Requirement: Periodic MongoDB Logging
Temperature and settings are persisted to the database at regular intervals and on every settings change.

#### Scenario: Interval-based logging
- **WHEN** the roast is active and 1 second has elapsed since the last log (`DB_LOG_INTERVAL_SECONDS = 1`)
- **THEN** the current temperature, RoR, fan, and power are logged to `temp_curve`

#### Scenario: Log on settings change
- **WHEN** the user changes fan or power
- **THEN** a `temp_curve` entry is immediately logged regardless of the interval timer

---

### Requirement: Quick Event Buttons
Pre-labeled buttons allow one-tap logging of standard roast milestones.

#### Scenario: Log quick event
- **WHEN** a user taps "Yellowing", "First Crack Start", "First Crack End", "Second Crack Start", or "Second Crack End"
- **THEN** a `key_timings` entry is created with the current elapsed time, temperature, fan, power, and RoR

#### Scenario: Auto-fill temperature in event
- **WHEN** a quick event is logged and the temperature field is empty
- **THEN** the current sensor temperature is used automatically

---

### Requirement: Local CSV Logging
Every second during an active roast, data is written to a local CSV file as a backup.

#### Scenario: CSV created on roast start
- **WHEN** a roast starts
- **THEN** a CSV file is created locally named after the roast ID

#### Scenario: Per-second CSV write
- **WHEN** the roast is active
- **THEN** elapsed time, temperature, RoR, fan, and power are appended to the CSV every second
