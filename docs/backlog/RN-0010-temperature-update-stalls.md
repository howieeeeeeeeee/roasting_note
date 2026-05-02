---
id: RN-0010
title: Temperature Sensor Updates Stall During Live Roast
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
  - connection-health
  - hardware
---

# Temperature Sensor Updates Stall During Live Roast

## Description

During a live roast, the temperature display is expected to refresh every second and make sensor failures obvious. In practice, the displayed temperature can appear stuck for more than 20 seconds, and the settings modal's **Test Connection** action sometimes fails several times before eventually connecting.

## Details

- The live roast frontend runs `syncState()` every 1 second with `setInterval(syncState, 1000)`.
- `syncState()` only updates the temperature display when `/api/roast/sync_state/<roast_id>` returns `success: true` and `temperature !== null`.
- If a sensor response is null after a previous successful reading, the UI keeps showing the previous temperature instead of clearly showing stale/offline sensor state.
- The settings modal's **Test Connection** action calls `/api/temp/current_fast`, which performs one fast sensor read; in real use it can require multiple manual retries before succeeding.
- The backend has two sensor read paths today:
  - `/api/temp/current_fast` uses one request with a 200ms timeout.
  - `/api/temp/current` and DB-log intervals use three requests with 100ms timeouts and require at least two successful readings.
- The ESP32 firmware exposes `/temp` and `/diagnostics`; hardware-side investigation is in scope if app-side diagnostics point to WiFi, sensor, firmware, or MAX31855 faults.
- A quick local DB scan found 24 active/non-archived roasts and 9 roasts with `temp_curve` gaps greater than 20 seconds.
- Example gaps from local DB:
  - `Taaroo`: gaps of 34s, 39s, 43s, 39s, 34s.
  - `Hulia`: gaps of 35s, 64s, 46s, 38s, 50s.
  - `Guji`: gaps of 59s, 62s, 43s, 47s, 50s.
  - Recent-looking examples also show gaps: `Bishan` 22s, `India` 23s/28s, `Passionfruit` 24s/34s, `Dark Guji Baku` 31s.
- One roast (`Taaroo Washed`) contains an abnormal negative timestamp gap from `-17098` to `3`, which suggests at least some historical temp data may include stale or corrupted client time.
- Database gaps only represent successful non-null readings today; null sensor reads are not persisted, so the DB cannot currently distinguish "poll failed" from "poll never happened".
- The fix should allow frequent local logging or diagnostics because local DB usage is the common workflow, while still keeping stored payloads reasonably small.
- Investigation should separate historical roasts from new roasts created after `DB_LOG_INTERVAL_SECONDS = 1`.
- Suspected causes include intermittent null sensor reads, browser timer throttling or iPad sleep, local network drops, slow ESP32 responses, overlapping `syncState()` requests, and hardware/firmware instability.

## Acceptance Criteria

- [ ] A failed or delayed temperature read during a live roast is visible as stale/offline state instead of silently leaving the last good temperature looking current.
- [ ] **Test Connection** no longer fails on a single transient sensor miss without context; it either retries internally or reports enough detail for the user to know whether to retry, check network, or inspect hardware.
- [ ] New diagnostic data can tell whether a >20s display stall came from sensor nulls, missed frontend polls, overlapping frontend requests, backend fetch duration, DB logging cadence, or hardware/firmware faults.
- [ ] Diagnostic logging is frequent enough for local troubleshooting during active live roasts, but bounded so it does not create excessive DB payload size.
- [ ] The implementation verifies the ESP32 `/diagnostics` path or equivalent hardware-side signal when app-side checks suggest hardware instability.
- [ ] New roast data either avoids >20s gaps during normal sensor operation or records enough diagnostics to explain them.
- [ ] Regression coverage or a manual QA checklist exists for sensor unavailable, delayed response, Test Connection retry, and hardware diagnostics cases.
- [ ] Relevant docs updated when implemented: `docs/features/live-roasting.md`, `docs/features/temperature-sensor.md`, `docs/design/screens/live-roasting.md`, `docs/hardware/thermo-sensor.md`, `docs/architecture/api-endpoints.md`, and `docs/architecture/data-models.md` if diagnostic payloads or persisted schema change.

## Open Questions

- What exact live-roast stale/offline UX should be used after repeated sensor misses? Answer: TBD.
- Should **Test Connection** auto-retry a fixed number of times, expose a manual retry with better status, or show a full diagnostic breakdown? Answer: TBD.
- What is the acceptable maximum diagnostic payload per active roast when using the local DB? Answer: Keep payload small where practical; exact limit TBD.
- Should diagnostics be embedded in each roast document, stored in a separate collection, written to local CSV, or split between DB and CSV? Answer: TBD.
- Which hardware-side failure modes should be tested first: WiFi reconnects, ESP32 response latency, MAX31855 error codes, thermocouple wiring, or power stability? Answer: TBD.

## Related Files

- `templates/roast_live.html`
- `templates/base.html`
- `app.py`
- `docs/features/live-roasting.md`
- `docs/features/temperature-sensor.md`
- `docs/hardware/thermo-sensor.md`
- `thermo/src/main.cpp`
- `docs/architecture/api-endpoints.md`
- `docs/architecture/data-models.md`
- `docs/design/screens/live-roasting.md`
- `tests/test_temperature_api.py`
- `tests/test_roasts_api.py`
