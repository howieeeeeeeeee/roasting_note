# Temperature Sensor Integration PRD

## Overview

Integrate a K-Type temperature sensor that provides real-time temperature readings via a local HTTP endpoint. Display current temperature on the live roast page and automatically log temperature readings with roast events.

## External Temperature Service

### Endpoint

- **URL:** Configured via environment variable `TEMP_SENSOR_URL` (e.g., `http://192.168.0.47/temp`)
- **Method:** GET
- **Response Format:**

  ```json
  {
    "temperatur_celsius": 73.75
  }
  ```

- **Availability:** Only returns data when the temperature service is running. Returns an error or no response when the service is off.

**Configuration:**

- The temperature sensor URL must be configured as an environment variable
- **Environment Variable Name:** `TEMP_SENSOR_URL`
- **Default Value (if not set):** `http://192.168.0.47/temp` (for backward compatibility during development)
- **Example:** `TEMP_SENSOR_URL=http://192.168.0.47/temp`

## Requirements

### 1. Temperature Display on Live Roast Page

**Location:** `/roast/live/<roast_id>`

**Display Conditions:**

- Show temperature only when roast status is:
  - **Not Started** (roast_start_time is null)
  - **Started** (roast_start_time exists, but roast_end_time is null)
- **Do NOT show and update** when roast is **Finished** (both roast_start_time and roast_end_time exist)

**Display Format:**

- Show temperature in Celsius (°C) beside the timing panel
- Format: `Temperature: XX°C` or similar
- Update automatically every 5 seconds

### 2. Temperature Retrieval Logic

**Polling Frequency:** Every 5 seconds

**Request Strategy:**
For each temperature update cycle:

1. Make **3 consecutive requests** to the temperature sensor URL (from `TEMP_SENSOR_URL` environment variable)
2. **Each request has a 0.1 second (100ms) timeout**
3. Collect all successful temperature values (requests that complete within timeout)
4. **If fewer than 2 successful values:** Return `null` to frontend (don't display temperature)
5. **If 2 or more successful values:**
   - Sort the values in descending order
   - Take the **two highest values**
   - Calculate the **average** of these two values
   - **Round to the nearest integer**
   - Display the rounded value on the frontend
6. **If all requests fail:** Return `null` to frontend, display "Sensor Offline"

**Error Handling & Timeout:**

- **Timeout:** Set request timeout to **0.1 seconds (100ms)** for each individual request
  - If no response is received within 0.1 seconds, consider the service unavailable
  - **Note:** For local network communication, 0.1 seconds should be reasonable (typical local network latency is 1-10ms, so 100ms provides ample buffer)
- If the service is unavailable (timeout, no response, or error):
  - Return `None` or `null` to the frontend (do not return a temperature value)
  - Display "N/A" or "Sensor Offline" instead of a temperature value on the frontend
  - Do not log automatic temperature events when service is unavailable
  - Continue polling attempts every 5 seconds
  - **Do not overwrite or modify existing temperature values** in any log events

### 3. Automatic Temperature Logging

**Architecture: Frontend-Triggered**

- Frontend polls `/api/temp/current` every 5 seconds for display
- Frontend immediately displays temperature (no DB lag)
- Frontend sends successful temperature readings to backend to log to DB

**When to Log:**

- Only log temperature to database when:
  - Roast is **started** (roast_start_time exists)
  - Temperature value is **valid** (successfully retrieved from sensor)
  - User has the live roast page open (frontend is active)

**Logging Behavior:**

- Each time temperature is successfully retrieved and displayed (within 0.1 second timeout):
  - Frontend immediately displays the temperature value
  - Frontend sends temperature reading to backend API (`POST /api/roast/add_event/<roast_id>`) to log to DB
  - Backend creates a temperature log entry in the `temp_curve` array
  - Include:
    - `time_seconds`: Current elapsed time since roast_start_time
    - `temperature`: The rounded integer temperature value
    - `fan_setting`: Current fan setting (if available, defaults to 0)
    - `power_setting`: Current power setting (if available, defaults to 0)
- **If temperature fetch fails** (timeout or error):
  - **Do not create** an automatic temperature log entry
  - **Do not overwrite** any existing log entries
  - Continue normal operation without logging temperature
- **If DB save fails** (network error, etc.):
  - Frontend should continue displaying temperature
  - Logging failure should not block display updates
  - Optionally log error to console for debugging

**Note:** This creates automatic temperature logs every 5 seconds during an active roast, but only when temperature is successfully retrieved and the frontend is active.

### 4. Temperature Logging with Manual Events

**When to Include Temperature:**
Every time a user manually logs an event (via API calls), automatically include the current temperature:

**Affected Events:**

- Power change events (`POST /api/roast/add_event/<roast_id>`)
- Key timing events (`POST /api/roast/add_timing/<roast_id>`)
- Any other manual log events

**Implementation:**

1. When a manual event is logged:
   - Check if the temperature input field is **empty**
   - If empty, make **one request** to the temperature sensor URL (from `TEMP_SENSOR_URL` environment variable) with **0.1 second timeout**
   - **If successful** (response received within timeout):
     - Include the temperature value (rounded to integer) in the event log entry
   - **If unsuccessful** (timeout, error, or no response):
     - **Still save the log event** (do not skip saving)
     - **Do not include temperature** in the event log entry (omit the temperature field entirely, or set to `null`)
     - **Do not overwrite** any existing temperature values
   - If the temperature input field already has a value, use that value instead (user override)
   - **Critical:** The event must be saved regardless of temperature fetch success/failure

**Frontend Behavior:**

- The temperature input field should **always start empty** (no default value)
- Do not pre-fill with the previous temperature value
- User can manually enter a temperature value if desired (which will override the sensor reading)

**Event Log Format:**

**For `key_timings` events:**

```json
{
  "event_name": "First Crack Start",
  "time_seconds": 542,
  "temperature": 190,  // Optional - automatically included from sensor if input empty
  "fan_setting": 3,    // Optional
  "power_setting": 4  // Optional
}
```

**For `temp_curve` events:**

```json
{
  "time_seconds": 542,
  "temperature": 190,  // Optional - automatically included from sensor if input empty
  "fan_setting": 0,    // Required (defaults to 0)
  "power_setting": 0,  // Required (defaults to 0)
  "note": "Optional note text"  // Optional
}
```

**Backend Schema Notes:**

- `key_timings` array: Currently supports optional `temperature`, `fan_setting`, `power_setting` ✅
- `temp_curve` array: Currently requires `temperature` (line 282 in app.py), but frontend can send `null` - **BACKEND NEEDS UPDATE** to handle optional temperature
- Both arrays store temperature as `float` type

### 5. Temperature Logging on Roast End

**When Ending a Roast:**

- When the "End Roast" button is clicked (`POST /api/roast/end/<roast_id>`):
  - Make **one request** to the temperature sensor URL (from `TEMP_SENSOR_URL` environment variable) with **0.1 second timeout** to get the final temperature
  - **If successful** (response received within timeout):
    - Create a final temperature log entry in the `temp_curve` array with:
      - `time_seconds`: Elapsed time since roast_start_time at the moment of ending
      - `temperature`: The rounded integer temperature value from sensor
      - `fan_setting`: Current fan setting (if available)
      - `power_setting`: Current power setting (if available)
  - **If unsuccessful** (timeout or error):
    - **Do not create** a final temperature log entry
    - **Do not overwrite** any existing log entries
    - Proceed with ending the roast normally (set `roast_end_time`)
  - This ensures the temperature curve includes the final reading before the roast ends, if available

### 6. Default Temperature Measurement Method

**Change Required:**

- Update the default value for `temp_measurement_method` field in new roasts
- **Old Default:** `"IR Gun"`
- **New Default:** `"K-Type Sensor V1"`

**Affected Locations:**

- `models/roast_helpers.py` - `create_draft_roast()` function (line 18)
  - Change: `'temp_measurement_method': 'IR Gun'` → `'temp_measurement_method': 'K-Type Sensor V1'`
- `models/roast_helpers.py` - `update_roast()` function (line 51)
  - Change: `'temp_measurement_method': roast_data.get('temp_measurement_method', 'IR Gun')` → `'temp_measurement_method': roast_data.get('temp_measurement_method', 'K-Type Sensor V1')`

## Technical Implementation Notes

### Backend API Endpoint (New)

Create a new endpoint to handle temperature retrieval:

**Endpoint:** `GET /api/temp/current`

- Reads temperature sensor URL from `TEMP_SENSOR_URL` environment variable
- Makes 3 consecutive requests to the configured temperature sensor URL
- **Each request has a 0.1 second (100ms) timeout**
- If any request times out or fails, mark that request as failed
- **Processing logic:**
  - Collect all successful temperature values (within timeout)
  - If fewer than 2 successful values, return `{"temperature": null, "status": "error", "message": "Insufficient readings"}`
  - If 2 or more successful values:
    - Sort values in descending order
    - Take the two highest values
    - Calculate average
    - Round to nearest integer
- **Return format:**
  - Success: `{"temperature": 190, "status": "success"}`
  - Error: `{"temperature": null, "status": "error", "message": "Service unavailable or timeout"}`
  - **Critical:** Always return `temperature: null` (not a number) when there's an error, so frontend can distinguish between valid temp and error state

**Environment Variable Setup:**

- Add `TEMP_SENSOR_URL` to `.env` file (for local development)
- Add `TEMP_SENSOR_URL` to Render environment variables (for production)
- Example: `TEMP_SENSOR_URL=http://192.168.0.47/temp`

### Frontend JavaScript

**Temperature Display & Logging Flow:**

1. **Display Polling:**
   - Use `setInterval()` to poll `/api/temp/current` every 5 seconds
   - **Handle response:**
     - If `status === "success"` and `temperature` is a number: Display temperature value immediately
     - If `status === "error"` or `temperature === null`: Display "N/A" or "Sensor Offline"
   - Update the temperature display element accordingly
   - **Do not overwrite** existing temperature values in the UI if the API returns an error
   - Continue polling even when errors occur (don't stop the polling interval)

2. **Automatic Logging to DB:**
   - After successfully displaying temperature, send it to backend to log:
     - Call `POST /api/roast/add_event/<roast_id>` with the temperature value
     - Include current `time_seconds` (from roast timer)
     - Include current `fan_setting` and `power_setting` if available (default to 0)
   - **Important:** Logging to DB should be non-blocking (use async/await or fire-and-forget)
   - If DB save fails, log error to console but don't interrupt display updates
   - Only log when roast is started (`roast_start_time` exists)

3. **Stop Polling:**
   - Stop temperature polling when roast is finished (`roast_end_time` exists)
   - Stop polling if user navigates away from live roast page

### Database Schema

**Current Schema (from codebase):**

**`key_timings` array structure:**

- `event_name` (String, required)
- `time_seconds` (Integer, required)
- `temperature` (Float, optional) - Currently supported ✅
- `fan_setting` (Integer, optional)
- `power_setting` (Integer, optional)

**`temp_curve` array structure:**

- `time_seconds` (Integer, required)
- `temperature` (Float, **currently required but should be optional**)
- `fan_setting` (Integer, required, defaults to 0)
- `power_setting` (Integer, required, defaults to 0)
- `note` (String, optional) - Already supported ✅

**Backend Changes Required:**

- Update `api_roast_add_event()` in `app.py` to handle `null` temperature values (currently line 282 will fail if `null` is passed)
- Change from: `'temperature': float(data['temperature'])`
- Change to: `'temperature': float(data['temperature']) if data.get('temperature') is not None else None`
- Then update the MongoDB push to conditionally include temperature: only add `temperature` field if value is not `None`

## Summary of Changes

### Frontend Changes

1. ⏳ Add temperature display to live roast page (for non-finished roasts)
2. ⏳ Implement 5-second polling with 3-request averaging logic (frontend-triggered)
3. ⏳ Auto-log temperature every 5 seconds during active roasts (frontend sends to backend after display)
4. ⏳ Include temperature in all manual event logs (only if input field is empty)
5. ✅ Frontend: Always keep temperature input field empty (no default to previous value) - **Already implemented**
6. ⏳ Log temperature when ending roast (final temperature reading)
7. ⏳ Stop temperature polling when roast is finished or user navigates away

### Backend Changes

8. ⏳ Change default `temp_measurement_method` to "K-Type Sensor V1" (update `models/roast_helpers.py`)
9. ⏳ Configure temperature sensor URL as environment variable `TEMP_SENSOR_URL`
10. ⏳ Create backend API endpoint `/api/temp/current` for temperature retrieval (reads from `TEMP_SENSOR_URL`)
11. ⏳ Update `api_roast_add_event()` to handle optional/null temperature values
12. ⏳ Update `api_roast_end()` to log final temperature reading (only if successful)
13. ⏳ Implement 0.1 second timeout for all temperature sensor requests
14. ⏳ Handle service unavailability gracefully:
    - Return `null` (not a number) when temp fetch fails
    - Save log events even if temp fetch fails (just without temperature field)
    - Do not overwrite existing temperature values
    - Do not create automatic temp logs when service is unavailable

### Current Implementation Status

- ✅ Temperature input field is cleared after events (line 458, 544 in `roast_live.html`)
- ✅ `key_timings` supports optional temperature (app.py line 257)
- ⚠️ `temp_curve` currently requires temperature but frontend can send null - **needs backend fix**
- ✅ `temp_curve` supports optional `note` field (app.py line 288)
- ⚠️ Default `temp_measurement_method` is "IR Gun" - **needs update to "K-Type Sensor V1"**
