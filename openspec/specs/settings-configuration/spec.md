
### Requirement: Sensor URL Configuration
The user can configure the URL of the temperature sensor at runtime.

#### Scenario: Set sensor URL
- **WHEN** POST `/api/settings/sensor` is called with `{"sensor_url": "http://..."}`
- **THEN** all subsequent temperature fetches use the provided URL

#### Scenario: Clear sensor URL reverts to default
- **WHEN** POST `/api/settings/sensor` is called with `{"sensor_url": ""}`
- **THEN** the sensor URL reverts to the default `http://192.168.0.47/temp`

#### Scenario: Get current sensor URL
- **WHEN** GET `/api/settings/sensor` is called
- **THEN** the current sensor URL is returned

---

### Requirement: Database Mode Configuration
The user can read and set the active database mode (local or online).

#### Scenario: Get current database mode
- **WHEN** GET `/api/settings/db` is called
- **THEN** the response includes `current_mode` and `default_mode`

#### Scenario: Set database mode
- **WHEN** POST `/api/settings/db` is called with `{"mode": "local"}` or `{"mode": "online"}`
- **THEN** the mode is updated in the session
- **AND** subsequent queries use the selected database

#### Scenario: Invalid mode rejected
- **WHEN** POST `/api/settings/db` is called with an unrecognized mode value
- **THEN** a 400 response is returned

---

### Requirement: Test Data Cleanup
Development and test environments can remove documents flagged as test data.

#### Scenario: Clean test data
- **WHEN** POST `/api/db/clean-test-data` is called
- **THEN** all beans and roasts in local database with `test_data: true` are deleted
- **AND** the response reports how many documents were removed

#### Scenario: Clean test data only affects local DB
- **WHEN** clean-test-data is called regardless of current session mode
- **THEN** only the local MongoDB instance is affected, never Atlas

---

### Requirement: Local Database Wipe
A destructive utility clears all data from the local database (for development/reset).

#### Scenario: Wipe local database
- **WHEN** POST `/api/db/clean-local` is called
- **THEN** all documents are deleted from the local `beans` and `roasts` collections
- **AND** the response confirms the wipe completed

#### Scenario: Wipe does not affect Atlas
- **WHEN** the local wipe runs
- **THEN** the Atlas database is not modified
