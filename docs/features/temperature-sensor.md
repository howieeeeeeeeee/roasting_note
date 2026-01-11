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

## API Endpoint

### GET /api/temp/current

Retrieves current temperature with retry logic.

**Process:**
1. Makes 3 consecutive requests to sensor URL
2. Each request has 100ms timeout
3. Collects successful readings
4. If < 2 readings: returns null
5. If >= 2 readings: returns average of two highest (rounded to integer)

**Success Response:**
```json
{
  "temperature": 185,
  "status": "success"
}
```

**Error Response:**
```json
{
  "temperature": null,
  "status": "error",
  "message": "Insufficient readings"
}
```

## Frontend Integration

### Display Polling

- Polls `/api/temp/current` every 5 seconds
- Updates temperature display immediately
- Shows "Offline" when sensor unavailable
- Continues polling on errors

### Automatic Database Logging

When temperature is successfully retrieved:
1. Display value immediately in UI
2. Send to backend to log in database
3. Create entry in `temp_curve` array
4. Include elapsed time, fan, power, RoR

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
| Sensor offline | Display "Offline", skip logging |
| Timeout | Treat as failed request |
| < 2 successful reads | Return null |
| DB save fails | Continue display, log error |

## Default Measurement Method

New roasts default to `"K-Type Sensor V1"` (changed from `"IR Gun"`).

Updated in:
- `models/roast_helpers.py` → `create_draft_roast()`
- `models/roast_helpers.py` → `update_roast()`
