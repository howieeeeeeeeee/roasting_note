# Live Roasting Interface

Real-time roasting control and monitoring at `/roast/live/<roast_id>`.

> **Design spec** — layout regions, top-bar tiles, chart/controls structure, and dark-mode behaviour are documented in [docs/design/screens/live-roasting.md](../design/screens/live-roasting.md).

## Overview

The live roasting page is the tablet-first interface used during an active roast. Timer, Temperature, Rate of Rise, and Since-FC readouts sit in a fixed top bar; the chart fills the main area; event buttons and Fan/Power controls live in a compact bottom strip.

## Features

### Timer Display

- Large MM:SS format in the Elapsed top-bar tile.
- "Since FC" tile appears automatically when First Crack Start is logged, showing development time elapsed.

### Temperature Display

- Real-time temperature from K-Type sensor.
- Syncs approximately every 1 second without overlapping requests.
- Uses bounded retries so normal ESP32 responses in the 200-450ms range do not
  appear as failures.
- Shows `Live`, `Retrying`, `Stale`, `Offline`, or `Sensor fault` under the
  temperature readout.
- Treats the last reading as stale after 5 seconds without a successful sensor
  read, and does not reuse stale temperature for event logging.

### Rate of Rise (RoR)

- Calculated using a configurable sliding window (default: 20 seconds).
- Settings in `app.py`: `ROR_WINDOW_SECONDS`, `ROR_TOLERANCE_SECONDS`.
- Formula: `(current_temp - past_temp) / time_diff × 60`.
- Finds closest reading within tolerance window (default: ±5 seconds).
- Displays after enough data is collected.
- Rounded to 1 decimal place.

### Fan & Power Controls

- Range: 1–9 for both settings.
- Default: Fan 9, Power 3.
- Direct +/– stepper buttons.

### Quick Event Buttons

| Button | Event Name |
| --- | --- |
| Y | Yellowing |
| FC | First Crack Start |
| FC-end | First Crack End |
| SC | Second Crack Start |
| SC-end | Second Crack End |

### Add Event Form

- Temperature input (auto-filled from sensor if empty).
- Optional note field.
- Logs to `temp_curve` array.

## Data Logging

### Automatic Logging

- Temperature fetched every 1 second with up to 3 attempts per sync.
- Logged to local CSV every second (`temp_logs/{roast_id}.csv`).
- Sensor read diagnostics logged locally every sync
  (`temp_logs/{roast_id}_sensor_diagnostics.csv`).
- Logged to database every second (configurable via `DB_LOG_INTERVAL_SECONDS`).
- RoR calculated and stored with each database entry.
- Successful `temp_curve` entries include sensor attempt counts and read
  duration. Non-`ok` sensor attempts are also stored in the bounded
  `sensor_diagnostics` array on the roast document.

### Manual Events

- Key timing events logged to `key_timings` array.
- Include current temperature and settings.

## Roast Lifecycle

1. **Pre-Start**: Setup section visible, timer at 00:00. Draft setup fields autosave to `/api/roast/update_setup/<roast_id>`.
2. **Start**: Click "Start Roast" → begins timer, starts polling.
3. **During**: Log events, adjust settings, monitor chart.
4. **End**: Click "End Roast" → stops timer, final temp logged.
5. **Post**: Redirected to Edit page for roasted weight entry.

Dashboard and bean-history links are lifecycle-aware:

- Draft roasts (`roast_start_time` and `roast_end_time` missing) open `/roast/live/<roast_id>` as **Resume Setup**.
- Active roasts (`roast_start_time` present, `roast_end_time` missing) open `/roast/live/<roast_id>` as **Resume Roast**.
- Completed roasts (`roast_end_time` present) open `/roast/detail/<roast_id>` as **View**.

## Dark Mode

Toggle via the moon icon in the navbar. Preference is persisted in `localStorage` under the key `roast-dark`. See [docs/design/foundations/dark-mode.md](../design/foundations/dark-mode.md) for the full system.
