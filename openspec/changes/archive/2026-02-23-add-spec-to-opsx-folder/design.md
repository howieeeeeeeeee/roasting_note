## Overview

This is a retroactive documentation change — no new code is written. The design section captures
the key technical decisions already embedded in the existing implementation, so future spec changes
have correct architectural context.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / Flask |
| Database | MongoDB (local) + MongoDB Atlas (cloud) |
| Frontend | Jinja2 templates + vanilla JS |
| Charting | Chart.js with annotation plugin |
| Package management | `uv` |
| Temperature sensor | ESP32 with K-Type thermocouple over HTTP |

## Data Model Highlights

### Roast document structure

```
roast {
  _id, title, roast_date, roaster_model, measurement_method
  bean_id (ref → beans._id)
  original_weight_grams, roasted_weight_grams, weight_loss_percent
  roast_start_time, roast_end_time, roast_duration_seconds
  key_timings: [{ event_name, time_seconds, temperature, fan, power, ror }]
  temp_curve:  [{ time_seconds, temperature, fan, power, ror, notes }]
  reviews:     [{ _id, overall_score, extraction_method, notes, created_at, updated_at }]
  archived, created_at, updated_at
}
```

### Bean document structure

```
bean {
  _id, name, origin, process, supplier
  purchase_date, price_total, weight_grams, stock_grams
  unit_price_per_kg (calculated)
  color, archived, created_at, updated_at
}
```

## Architectural Decisions

### Embedded documents for reviews and timing
Reviews, key timings, and temp curve are stored as embedded arrays in the roast document rather
than separate collections. This keeps all roast data in a single read and simplifies queries.

### Dual-write temperature logging
Temperature is written to both a local CSV (every second) and MongoDB (every 5 seconds + on
settings change). CSV is a low-latency fallback; MongoDB is the source of truth for charts.

### Session-based settings
Sensor URL and database mode are stored in the Flask session (not persisted to DB). This means
settings reset on server restart, which is acceptable for a local-first tool.

### Soft deletion everywhere
Both beans and roasts use `archived: true` for deletion. Hard deletes are never performed on
user data. Wipe and clean utilities are development-only.

### Stock management via application logic
Bean stock adjustments happen in Flask route handlers, not as MongoDB triggers or transactions.
This is acceptable for a single-user local application with low concurrency risk.

### RoR in-memory deque
RoR calculation uses a Python `deque(maxlen=60)` for a rolling 60-second window held in process
memory. This resets on server restart. The DB-stored RoR values in `temp_curve` are the durable
record.
