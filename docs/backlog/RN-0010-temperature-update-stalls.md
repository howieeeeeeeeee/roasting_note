---
id: RN-0010
title: Temperature Updates Stall During Live Roast
type: bug
status: pending
priority: high
created: 2026-04-24
resolved:
area: live-roasting
tags:
  - temperature-sensor
  - polling
  - database-logging
---

# Temperature Updates Stall During Live Roast

## Description

During a live roast, the temperature display is expected to refresh frequently. The current live page calls `/api/roast/sync_state/<roast_id>` every 1 second, and the database logging interval is configured as `DB_LOG_INTERVAL_SECONDS = 1`. In practice, the displayed temperature sometimes appears stuck for more than 20 seconds.

## Current Evidence

- The live roast frontend runs `syncState()` every 1 second with `setInterval(syncState, 1000)`.
- `syncState()` only updates the temperature display when the response has `success: true` and `temperature !== null`.
- If the sensor response is null after a previous successful reading, the UI keeps showing the previous temperature instead of making the stall obvious.
- A quick local DB scan found 24 active/non-archived roasts and 9 roasts with `temp_curve` gaps greater than 20 seconds.
- Example gaps from local DB:
  - `Taaroo`: gaps of 34s, 39s, 43s, 39s, 34s.
  - `Hulia`: gaps of 35s, 64s, 46s, 38s, 50s.
  - `Guji`: gaps of 59s, 62s, 43s, 47s, 50s.
  - Recent-looking examples also show gaps: `Bishan` 22s, `India` 23s/28s, `Passionfruit` 24s/34s, `Dark Guji Baku` 31s.
- One roast (`Taaroo Washed`) contains an abnormal negative timestamp gap from `-17098` to `3`, which suggests at least some historical temp data may include stale or corrupted client time.

## Suspected Causes To Investigate

- Sensor reads may be intermittently returning null, and the frontend masks that by keeping the last successful temperature visible.
- Browser timer throttling, tablet sleep, network drops, or backgrounding Safari may delay the 1-second polling loop.
- The backend fetch path may block or queue requests if the temperature sensor is slow or unreliable.
- `syncState()` requests may overlap because the frontend uses `setInterval` with an async function and does not guard against an in-flight request.
- Database gaps only represent successful non-null readings; null sensor readings are not persisted, so the DB cannot currently distinguish "poll failed" from "poll never happened".
- Historical roasts may include data from older logging intervals, so the investigation should separate old data from new roasts after `DB_LOG_INTERVAL_SECONDS = 1`.

## Investigation Plan

1. Add client-side visibility for stale readings:
   - Track the last successful temperature update timestamp.
   - Show a stale/offline indicator if no successful temperature arrives for more than 3-5 seconds.
2. Instrument `/api/roast/sync_state/<roast_id>` to record or log:
   - Request arrival time.
   - Sensor fetch duration.
   - Whether temperature was null.
   - Whether the event was logged to DB.
3. Review local CSV logs for affected roasts and compare them with MongoDB `temp_curve` gaps.
4. Reproduce during a roast or simulated sensor outage:
   - Sensor available.
   - Sensor intermittently unavailable.
   - Browser tab backgrounded or iPad screen dimmed.
5. Decide whether to:
   - Prevent overlapping sync requests.
   - Persist null/stale samples or separate poll health events.
   - Add a visible "stale data" warning.
   - Add retry/backoff or sensor health diagnostics.

## Acceptance Criteria

- [ ] We can tell whether a >20s display stall is caused by sensor nulls, missed frontend polls, backend slowness, or DB logging gaps.
- [ ] Live roast UI clearly indicates stale/offline temperature instead of silently showing an old value.
- [ ] New roast data either avoids >20s gaps during normal sensor operation or records enough diagnostics to explain them.
- [ ] Regression coverage or a manual QA checklist exists for sensor unavailable and delayed response cases.

## Related Files

- `templates/roast_live.html`
- `app.py`
- `docs/features/live-roasting.md`
- `tests/test_temperature_api.py`
- `tests/test_roasts_api.py`
