---
id: RN-0003
title: In-App Browser and API Workflow Testing
type: improvement
status: pending
priority: medium
created: 2026-01-11
resolved:
area: testing
parent:
decisions: []
blocked_by: []
tags:
  - ui
  - e2e
  - in-app-browser
  - api
  - virtual-sensor
---

# In-App Browser and API Workflow Testing

## Description

Create a repeatable Codex in-app-browser workflow for the real RoastLogger UI,
backed by a dedicated E2E database and deterministic virtual temperature
sensor. Strengthen pytest API coverage at the same time so browser failures can
be diagnosed against stable backend contracts without requiring the physical
sensor board.

## Details

### Dependency

- RN-0018 and RN-0022 are resolved. The E2E harness starts from the delivered
  app factory/configuration boundary, injectable local database name and sensor
  URL, modular live-roast JavaScript, route regression baseline, and guarded
  fail-closed synchronization contract.

### Browser-Test Approach

- Use Codex's in-app browser to exercise the visible local application as a
  user would: navigate, click, type, inspect rendered state, capture
  screenshots, and review browser console/network failures.
- Add a durable runbook and local harness, not Playwright, Selenium, or Cypress.
  No standalone browser automation dependency or CI browser matrix is in
  scope.
- Once the documented local services are available, an agent must be able to
  complete preflight, workflows, evidence capture, and cleanup without human
  intervention.

### Dedicated E2E Runtime And Data

- Add an explicit E2E configuration using `E2E_MODE`, `E2E_RUN_ID`, and
  `LOCAL_DB_NAME=roastlogger_e2e`. The normal database name remains
  `roastlogger`.
- E2E mode must force local mode, skip initialization/use of the online
  database, reject database-mode changes to online, and reject both sync
  directions.
- Every bean and roast created through the E2E browser session must
  automatically include `test_data: true` and the current `test_run_id`.
  Updates must retain both markers.
- Provide one documented start command and a run-scoped cleanup command, for
  example:
  - `uv run python -m tests.e2e.manage start --run-id <id>`
  - `uv run python -m tests.e2e.manage cleanup --run-id <id>`
- Cleanup must delete only the selected run's roasts, then beans, then both
  `{roast_id}.csv` and `{roast_id}_sensor_diagnostics.csv`. It must report
  counts and verify that no selected-run records remain.
- Cleanup and startup must refuse to operate when the configured database name
  is not exactly `roastlogger_e2e`. Do not register test-control or cleanup
  routes in a normal application instance.

### Virtual Temperature Sensor

- Run a lightweight sensor service on `127.0.0.1` only. It must implement the
  ESP32-compatible `GET /temp` and `GET /diagnostics` contracts.
- Expose a loopback-only test control used by the harness to select these
  deterministic scenarios:

| Scenario | Required behavior |
| --- | --- |
| `healthy-ramp` | Return a repeatable increasing Celsius curve suitable for chart and RoR checks |
| `slow-success` | Return valid readings after a realistic delay below the live timeout |
| `rate-limited` | Return HTTP 429 for a configured number of calls, then recover |
| `timeout` | Delay beyond the configured request timeout |
| `offline` | Return a deterministic unavailable response |
| `malformed` | Return invalid JSON or omit the temperature field |
| `fault` | Fail temperature reads and return thermocouple fault bits from `/diagnostics` |

- Scenario changes must not require restarting RoastLogger. The runbook must
  state the expected UI/API state for retrying, stale, offline, fault, and
  recovered readings.

### In-App Browser Workflows

1. Start an E2E run and confirm the app reports local E2E configuration and the
   virtual sensor connection.
2. Create a uniquely named bean through the UI, confirm it appears in the
   inventory/detail pages, edit multiple fields, and verify the update.
3. Create a roast, select the test bean, enter green weight and ambient data,
   start it, and verify the timer starts and bean stock is deducted once.
4. Under `healthy-ramp`, verify temperature and RoR updates, chart points
   render, and polling does not overlap.
5. Change fan/power, log Yellowing and First Crack events, add a note event,
   and verify the timeline and chart annotations update.
6. Exercise rate limiting/retry, stale or offline, recovery, and fault
   scenarios. Verify status labels, continued polling, bounded diagnostics,
   and recovery to live readings.
7. End the roast, verify the redirect to the edit page, save post-roast data,
   and confirm the detail page and stored roast curve/events.
8. Capture an optional review create/update/delete smoke check separately; it
   is useful evidence but not a release gate for the core workflow.
9. Run scoped cleanup and prove the run's records and temperature logs were
   removed without touching any other data.

### API Coverage Completion

- Add a route-manifest assertion covering every page and API route, method, and
  endpoint so RN-0018 cannot silently drop a route.
- Add direct success and failure coverage for current gaps: label image and
  preference APIs, database settings, both sync route wrappers, test-data
  cleanup, local-clean safety, and remaining page-render routes.
- Add consistent invalid ObjectId, missing/malformed payload, not-found,
  lifecycle-conflict, and database-safety cases where each contract applies.
- Test E2E-mode safeguards, automatic test markers, run-scoped cleanup, and
  refusal to touch a non-E2E database.
- Contract-test every virtual-sensor scenario and integrate representative
  scenarios through the RoastLogger temperature and live-sync APIs.
- Any application defect exposed by the new tests must be fixed under a
  focused follow-up ticket unless it is a small correction required to satisfy
  an already documented API contract.

### Evidence And Failure Diagnosis

- Store screenshots, a concise Markdown run summary, console errors, and failed
  network requests under a run-specific ignored artifacts directory.
- The summary must record run ID, commit, app/sensor URLs, scenarios exercised,
  assertions passed/failed, cleanup counts, and links to evidence.
- A failed run must preserve enough evidence for diagnosis while cleanup
  remains safe to run independently.

### Out Of Scope

- Playwright, Selenium, Cypress, unattended CI browser execution, and
  multi-browser matrices.
- Production test-control endpoints or any path that can select the online
  database from E2E mode.
- Replacing focused API tests with browser checks.

## Acceptance Criteria

- [ ] The documented E2E start command launches RoastLogger against only `roastlogger_e2e`, assigns a unique run ID, and points it at the loopback virtual sensor.
- [ ] Browser-created beans and roasts receive `test_data: true` plus the current `test_run_id`, and updates retain both markers.
- [ ] E2E mode cannot select, initialize, or synchronize with the online database.
- [ ] Run-scoped cleanup refuses non-E2E databases and removes only the selected run's roasts, beans, temperature CSVs, and diagnostic CSVs.
- [ ] The virtual sensor implements `/temp`, `/diagnostics`, and every deterministic scenario defined above, including HTTP 429 followed by recovery.
- [ ] The in-app-browser runbook completes the bean and live-roast workflows, verifies chart/control/sensor states, captures diagnostic evidence, and finishes with safe cleanup.
- [ ] The route manifest and expanded API tests cover the listed route gaps, validation/failure contracts, E2E safeguards, cleanup, and sensor integration.
- [ ] The existing API suite and all new focused tests pass with `uv run pytest`.
- [ ] No Playwright, Selenium, Cypress, production test-control route, or CI browser dependency is added.
- [ ] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Documentation Impact

- `tests/README.md`
- `tests/e2e/README.md` (new)
- `docs/architecture/data-models.md`
- `docs/architecture/tech-stack.md`
- `docs/features/temperature-sensor.md`
- `docs/features/live-roasting.md`
- Conditional: `docs/architecture/api-endpoints.md` if satisfying an exposed
  contract requires changing a production route.
- Conditional: `docs/design/screens/live-roasting.md` only if browser
  verification exposes and implementation changes a visible interaction.

## Open Questions

- None. The in-app-browser approach, Playwright exclusion, dedicated E2E
  database, run-scoped markers/cleanup, and virtual-sensor scenarios are
  decided.

## Related Files

- `tests/conftest.py`
- `tests/cleanup_test_data.py`
- `tests/README.md`
- `tests/test_beans_api.py`
- `tests/test_roasts_api.py`
- `tests/test_temperature_api.py`
- `tests/test_sync_api.py`
- `app.py`
- `templates/roast_live.html`
- `templates/beans_form.html`
- `templates/beans_list.html`
- `templates/roast_edit.html`
- `templates/roast_detail.html`
- `static/js/roast-chart.js`
- `docs/architecture/data-models.md`
- `docs/architecture/tech-stack.md`
- `docs/features/temperature-sensor.md`
- `docs/features/live-roasting.md`
