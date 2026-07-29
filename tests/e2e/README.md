# Codex In-App-Browser E2E Runbook

This runbook exercises the real RoastLogger UI with a dedicated local database
and deterministic virtual temperature sensor. It does not use Playwright,
Selenium, Cypress, a production test-control route, or an online database.

## Safety Invariants

- E2E mode requires `LOCAL_DB_NAME=roastlogger_e2e`.
- Local MongoDB and the virtual sensor must use loopback hosts.
- E2E startup constructs only the local MongoDB client. It places a disabled
  placeholder in `MONGO_URI`; the app never initializes or accesses it.
- E2E mode forces local database selection and rejects online selection,
  historic sync mutation routes, sync preflight execution, and global cleanup.
- Settings sync-button clicks still create sanitized terminal intent audits,
  but those records live inside ignored run artifacts.
- Browser-created beans and roasts receive `test_data: true` and the exact
  `test_run_id`. Updates retain both fields.
- All logs, screenshots, summaries, and service output stay under ignored
  `tests/e2e/artifacts/<run-id>/`.

## Start

Prerequisites are local MongoDB, project dependencies installed with `uv`, and
free loopback ports 5011 and 5012.

Choose a new run ID containing only letters, numbers, underscores, and hyphens.
Run this in a dedicated terminal and leave it active:

```bash
uv run python -m tests.e2e.manage start \
  --run-id codex-20260729-a
```

The command starts:

- RoastLogger: `http://127.0.0.1:5011`
- virtual sensor: `http://127.0.0.1:5012/temp`
- sensor control: `POST http://127.0.0.1:5012/__e2e/scenario`

It prints the run ID, URLs, and ignored artifact path after both services are
healthy. Startup fails if the run ID already has artifacts or the database name
is not exactly `roastlogger_e2e`.

Before opening the browser, verify the runtime:

```bash
curl -s http://127.0.0.1:5011/api/settings/db
curl -s http://127.0.0.1:5011/api/temp/test_connection
```

The database response must report `e2e_mode: true`, `mode: local`,
`local_database: roastlogger_e2e`, and the selected run ID.

## Sensor Scenario Control

Change scenarios without restarting either service:

```bash
curl -s -X POST http://127.0.0.1:5012/__e2e/scenario \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"healthy-ramp"}'
```

Supported scenarios and expected application state:

| Scenario | Sensor contract | Expected RoastLogger state |
| --- | --- | --- |
| `healthy-ramp` | Repeatable +2.5°C readings | `Live`, temperature/chart advance, RoR appears after its window |
| `slow-success` | Valid response after 200ms | Remains `Live`; polling requests do not overlap |
| `rate-limited` | Configured HTTP 429 calls, then valid readings | `Retrying`, then recovery to `Live` |
| `timeout` | Response after the configured app timeout | `Retrying`, then `Stale` after five client seconds |
| `offline` | HTTP 503 | `Offline` before any success; polling continues |
| `malformed` | Invalid JSON | Credential-free invalid-data error and continued polling |
| `fault` | Failed temperature plus MAX31855 fault diagnostics | `Sensor fault`, bounded diagnostic history |

Configure the rate-limited call count when needed:

```bash
curl -s -X POST http://127.0.0.1:5012/__e2e/scenario \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"rate-limited","rate_limit_calls":2}'
```

The control endpoint rejects non-loopback clients.

## Codex In-App-Browser Workflow

Use Codex's in-app browser, not a standalone browser driver.

### Preflight And Fail-Closed Sync

1. Open `http://127.0.0.1:5011`.
2. Open Settings and confirm the database label contains
   `local (roastlogger_e2e / <run-id>)`.
3. Confirm the Online radio is disabled.
4. Click **Preview Online → Local**. The result must prominently say sync
   preflight is disabled in E2E mode and show an artifact-local audit path.
5. In the browser network view, confirm the preflight request is `503`.
6. If directly checking the historic POST sync URLs, confirm `409`. Neither
   path may create `db_backup/` or access an online database.

### Bean

1. Navigate to **Beans**, choose **Add Bean**, and use a run-unique name.
2. Fill origin, process, supplier, purchase date, price, purchase weight,
   stock, flavor notes, notes, and color; save.
3. Confirm the bean appears in inventory and its detail page.
4. Edit several fields and save.
5. Reopen detail and confirm the changes.

### Live Roast

1. Choose **New Roast**, select the test bean, set a run-unique title, green
   weight, ambient temperature, and humidity.
2. Start the roast. Confirm the timer advances and bean stock is deducted
   exactly once.
3. Set `healthy-ramp`. Confirm temperature, RoR, and chart points update.
   Inspect network timing long enough to confirm at most one
   `/api/roast/sync_state/` request is pending.
4. Change fan and power. Log Yellowing, First Crack, and one note event.
   Confirm timeline entries and chart annotations.
5. Exercise `rate-limited`, `timeout` or `offline`, recovery through
   `healthy-ramp`, and `fault`. Confirm the state labels in the table above,
   continued polling, and recovery.
6. End the roast, verify redirect to Edit, add roasted weight and notes, save,
   and inspect Detail for curve/events and weight-loss data.
7. Optionally smoke-test review create/update/delete; it is not a release gate.

## Evidence

The start command creates:

```text
tests/e2e/artifacts/<run-id>/
├── summary.md
├── screenshots/
├── app.log
├── sensor.log
├── temp_logs/
└── docs/audit_history/...
```

Save screenshots for Settings safety, bean detail, live healthy state,
retry/offline/fault state, and final roast detail. Update `summary.md` with:

- scenarios exercised;
- browser assertions passed or failed;
- console errors;
- failed network requests;
- cleanup counts; and
- relative links to screenshots.

On failure, preserve artifacts and service logs. Cleanup is independent and
safe to run later.

## Stop And Clean Up

Stop the foreground start command with Ctrl-C. Then delete only the chosen
run:

```bash
uv run python -m tests.e2e.manage cleanup \
  --run-id codex-20260729-a
```

Cleanup deletes selected-run roasts first, then beans, then
`{roast_id}.csv` and `{roast_id}_sensor_diagnostics.csv`. It verifies zero
selected-run records remain and reports counts. It refuses any database name
other than `roastlogger_e2e`.

Before committing, verify artifacts and E2E data are absent from Git:

```bash
git status --short
git ls-files tests/e2e/artifacts tests/e2e/runtime db_backup
```
