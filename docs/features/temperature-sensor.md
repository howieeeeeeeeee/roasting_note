# Temperature Sensor Integration

K-Type thermocouple sensor integration for real-time temperature monitoring.

## Hardware

- **Sensor:** MAX31855 K-Type Thermocouple
- **Controller:** ESP32 microcontroller
- **Documentation:** See `docs/hardware/thermo-sensor.md`

## Configuration

### Environment Variable

```
TEMP_SENSOR_URL=http://192.168.0.47/temp
```

### Sensor Response Format

```json
{
  "temperature_celsius": 185.50,
  "temperature_fahrenheit": 365.90
}
```

Note: Code handles both `temperature_celsius` and `temperatur_celsius` for compatibility.

## API Endpoints

### GET /api/temp/current_fast

Single-attempt fetch for lightweight checks.

**Process:**
1. Makes 1 request to sensor URL with the standard live timeout
2. Returns temperature immediately on success, or `null` on failure

**Response format is the same as `/api/temp/current`.**

---

### GET /api/temp/current

Accurate temperature fetch with retry logic.

**Process:**
1. Makes 3 consecutive requests to sensor URL
2. Each request uses the standard live timeout
3. Collects successful readings
4. If < 2 readings: returns null
5. If >= 2 readings: returns average of two highest (rounded to integer)

**Success Response:**
```json
{
  "temperature": 185,
  "status": "success",
  "sensor_status": "ok",
  "attempts": 3,
  "successes": 3,
  "duration_ms": 640
}
```

**Error Response:**
```json
{
  "temperature": null,
  "status": "error",
  "sensor_status": "offline",
  "attempts": 3,
  "successes": 0,
  "duration_ms": 2250,
  "message": "timeout"
}
```

### GET /api/temp/test_connection

Settings-modal connection test. It retries internally and checks the ESP32
`/diagnostics` endpoint when temperature reads fail. The response includes the
same fields as `/api/temp/current`, plus `diagnostics` when available.

## Frontend Integration

### Display Polling

- Polls `/api/roast/sync_state/<roast_id>` approximately every 1 second
  without overlapping requests.
- Backend sync uses up to 3 attempts and accepts 1 successful reading for live
  logging.
- Updates temperature display immediately when a fresh reading arrives.
- Shows retrying, stale, offline, or fault state when reads fail.
- Marks a reading stale after 5 seconds without sensor success.
- Continues polling on errors.

### Automatic Database Logging

When temperature is successfully retrieved:
1. Display value immediately in UI
2. Send to backend to log in database
3. Create entry in `temp_curve` array
4. Include elapsed time, fan, power, RoR
5. Include sensor status, attempts, successes, and read duration

**Only logs when:**
- Roast has started
- Temperature is valid
- Live page is active

### Manual Event Integration

When user logs events (key timings, power changes):
1. Check if temperature input field is empty
2. If empty: fetch from sensor (100ms timeout)
3. Include temperature if successful
4. Save event regardless of sensor availability

## Local CSV Logging

For detailed analysis, temperatures are also logged locally:

- **Directory:** `temp_logs/`
- **Filename:** `{roast_id}.csv`
- **Format:** `time_seconds,temperature`
- **Frequency:** Every second during active roast

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Sensor offline | Display `Offline`, skip temperature logging, store anomaly diagnostics |
| Timeout after a previous reading | Display `Retrying` until the last success is 5 seconds old, then `Stale` |
| ESP32 diagnostics fault | Display `Sensor fault`, include diagnostic error bits |
| < 2 successful reads on `/api/temp/current` | Return null with retry metadata |
| DB save fails | Continue display, log error |

## Default Measurement Method

New roasts default to `"K-Type Sensor V1"` (changed from `"IR Gun"`).

Updated in:
- `models/roast_helpers.py` → `create_draft_roast()`
- `models/roast_helpers.py` → `update_roast()`
