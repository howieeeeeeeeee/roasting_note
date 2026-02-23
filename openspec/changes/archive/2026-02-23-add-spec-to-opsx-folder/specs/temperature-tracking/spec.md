## ADDED Requirements

### Requirement: Accurate Temperature Read
The system fetches temperature from the K-Type sensor using a multi-request averaging strategy to reduce noise.

#### Scenario: Averaging read succeeds with 3 responses
- **WHEN** GET `/api/temp/current` is called
- **THEN** 3 consecutive requests are made to the sensor URL with 100ms timeout each
- **AND** the top 2 highest readings are averaged
- **AND** the averaged temperature is returned

#### Scenario: Averaging read succeeds with 2 responses
- **WHEN** only 2 of the 3 requests succeed
- **THEN** both readings are averaged and returned

#### Scenario: Averaging read fails with fewer than 2 responses
- **WHEN** fewer than 2 requests succeed
- **THEN** `temperature` is returned as `null`

#### Scenario: Sensor timeout
- **WHEN** the sensor does not respond within 100ms
- **THEN** that request is counted as a failure and excluded from the average

---

### Requirement: Fast Temperature Read
A low-latency single-request endpoint is available for UI polling.

#### Scenario: Fast read returns current temperature
- **WHEN** GET `/api/temp/current_fast` is called
- **THEN** a single request is made to the sensor with 200ms timeout
- **AND** the temperature is returned immediately without averaging

#### Scenario: Fast read on sensor failure
- **WHEN** the sensor does not respond
- **THEN** `temperature` is returned as `null` and no error is raised

---

### Requirement: Rate of Rise (RoR) Calculation
RoR is computed from a sliding window of historical temperature readings.

#### Scenario: RoR calculation with sufficient history
- **WHEN** the roast has at least `ROR_WINDOW_SECONDS` (20s) of temperature data
- **THEN** RoR is calculated as `(current_temp - window_temp) / time_diff * 60` in °C/min
- **AND** the result is rounded to 1 decimal place

#### Scenario: RoR window matching
- **WHEN** finding the reference temperature at `now - ROR_WINDOW_SECONDS`
- **THEN** the closest reading within ±`ROR_TOLERANCE_SECONDS` (5s) is used

#### Scenario: RoR with insufficient history
- **WHEN** fewer than `ROR_WINDOW_SECONDS` of data are available
- **THEN** RoR is returned as `null`

#### Scenario: RoR spike suppression
- **WHEN** calculated RoR exceeds 30°C/min
- **THEN** it is filtered out of chart display to prevent distortion

---

### Requirement: Sensor Offline Handling
The live interface continues operating when the sensor is unavailable.

#### Scenario: Sensor offline during roast
- **WHEN** the sensor is offline or returns invalid data
- **THEN** the UI displays "Offline" for the temperature field
- **AND** the roast timer and event logging continue to function normally
- **AND** temperature fields in logged events are set to `null`
