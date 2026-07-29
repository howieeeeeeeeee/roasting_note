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
- Logged to the configured local log directory every second
  (`{TEMP_LOG_DIR}/{roast_id}.csv`; normal default `temp_logs/`).
- Sensor read diagnostics logged locally every sync
  (`temp_logs/{roast_id}_sensor_diagnostics.csv`).
- Logged to database every second (configurable via `DB_LOG_INTERVAL_SECONDS`).
- RoR calculated and stored with each database entry.
- Successful `temp_curve` entries include sensor attempt counts and read
  duration. Non-`ok` sensor attempts are also stored in the bounded
  `sensor_diagnostics` array on the roast document.

The E2E runtime redirects both CSV files into its ignored run artifact
directory. The virtual sensor exercises healthy, slow, rate-limited, timeout,
offline, malformed, fault, and recovered states without physical hardware.
See [the Codex in-app-browser runbook](../../tests/e2e/README.md).

### Browser Module Boundary

`templates/roast_live.html` keeps the server-rendered markup and existing DOM
identifiers. Jinja-derived runtime state is encoded once in the
`live-roast-config` JSON script element. `static/js/live-roast/index.js` reads
that bootstrap and composes focused chart, session/polling, and fullscreen
modules. The polling module schedules the next one-second request only after
the current request completes, so requests do not overlap.

### Manual Events

- Key timing events logged to `key_timings` array.
- Include current temperature and settings.

## Roast Lifecycle

New and updated roasts store an explicit `lifecycle_status` value. Lifecycle
state and mutation behavior is implemented by focused services used by the
roast route blueprint:
`draft`, `started`, or `completed`. Older roasts without this field fall back
to timestamp-derived lifecycle:

- `roast_end_time` present -> completed.
- `roast_start_time` present and no `roast_end_time` -> started.
- Neither timestamp present -> draft.

1. **Pre-Start**: Setup section visible, timer at 00:00. Draft setup fields autosave to `/api/roast/update_setup/<roast_id>`.
2. **Start**: Click "Start Roast" -> begins timer, starts polling, writes `lifecycle_status: "started"`, and deducts bean stock when bean/weight are provided.
3. **During**: Log events, adjust settings, monitor chart.
4. **End**: Click "End Roast" -> stops timer, final temp logged, writes `lifecycle_status: "completed"`.
5. **Manual Complete**: Draft-only **Set to Completed** writes `lifecycle_status: "completed"` and refreshes `updated_at` without creating `roast_start_time`, `roast_end_time`, temperature curve readings, sensor diagnostics, key timing events, a Drop event, or bean-stock adjustments.
6. **Post**: Live ending and manual completion redirect to Edit page for roasted weight entry.

Dashboard and bean-history links are lifecycle-aware:

- Draft roasts open `/roast/live/<roast_id>` as **Resume Setup**.
- Started roasts open `/roast/live/<roast_id>` as **Resume Roast** and display as **In Progress**.
- Completed roasts open `/roast/detail/<roast_id>` as **View**, even when they were manually completed without live-roast timing data.

### Timestamp Display

Roast list, bean-history, roast detail, and review timestamps render in the
configured operator timezone (`TIMEZONE`, default `America/New_York`). MongoDB
BSON dates are stored as UTC instants, and PyMongo returns them as naive UTC
datetimes by default, so display formatting interprets naive datetimes as UTC
before converting them for the operator. Duration and elapsed-time calculations
remain based on start/end deltas and are not shifted for display.

## Dark Mode

Toggle via the moon icon in the navbar. Preference is persisted in `localStorage` under the key `roast-dark`. See [docs/design/foundations/dark-mode.md](../design/foundations/dark-mode.md) for the full system.
