# Codex In-App-Browser E2E Runbook

This runbook exercises the real RoastLogger UI with a dedicated local database
and deterministic virtual temperature sensor. It does not use Playwright,
Selenium, Cypress, a production test-control route, or an online database.

## Maintaining The UI Checklist

This file is the canonical durable UI regression checklist. Do not copy its
changing scenario list into ticket skills or ticket records.

This checklist applies to ticket browser levels `targeted` and `full`. For every
new or changed visible UI interaction at either level:

1. Record the exact scenario to add or update under the ticket's
   `## Testing Impact`.
2. Add the user entry point, action, observable success state, important
   failure state, and required screenshot or log evidence to the relevant
   workflow below. Add a focused subsection when no current workflow fits.
3. Add automated API or contract coverage where practical. Browser checks
   supplement automated tests; they do not replace them.
4. Run the targeted scenario during implementation. Run the complete affected
   workflow for cross-screen changes and critical live roast, sensor, stock,
   Settings, or sync behavior.
5. Update or remove obsolete steps when UI behavior changes or is removed.

A small visual-only correction may use browser level `none` with a concrete
ticket reason; it needs no browser run or checklist change. Use `targeted` with
a screenshot when the change can hide content, affect responsive layout, or
alter a shared component. Use `full` only when behavior spans a critical or
cross-screen workflow.

## Safety Invariants

- E2E mode requires `LOCAL_DB_NAME=roastlogger_e2e`.
- Local MongoDB and the virtual sensor must use loopback hosts.
- E2E startup constructs only the local MongoDB client. It places a disabled
  placeholder in `MONGO_URI`; the app never initializes or accesses it.
- E2E mode forces local database selection and rejects online selection,
  historic sync mutation routes, and global cleanup.
- Ordinary E2E rejects sync preflight and every browser phase route. Settings
  sync-button clicks still create sanitized terminal intent audits inside
  ignored run artifacts.
- Guarded-sync success coverage requires the explicit `--sync-fake` start
  option. Its injected executor refuses non-artifact roots, never constructs or
  uses an online MongoDB client, and records `database_access: false` for every
  simulated phase.
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

For the guarded local Settings simulation, use a new run and explicitly inject
the safe executor:

```bash
uv run python -m tests.e2e.manage start \
  --run-id rn-0028-settings-sync-a \
  --sync-fake
```

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

### Quiet Compact UI

#### Foundations

1. Start run `rn-0029-foundations-a` and open Roasts, Beans, Add Bean,
   Settings, and the live-roast shell at `1440x900` and `1024x768`.
2. Repeat representative views in light and dark modes. Confirm small labels,
   placeholders, inactive navigation, and table headings remain readable.
3. Inspect computed fonts and network requests. Ordinary pages use Inter,
   Raleway, DM Mono, and Material Icons without a duplicate stylesheet
   request. Bean detail loads the three additional label faces before canvas
   drawing.
4. Measure representative management controls at 44px or larger and live-roast
   controls at 54px or larger. Confirm the chart and instrument values retain
   their previous geometry.
5. Save representative light/dark screenshots and record font requests,
   computed text colors, target measurements, console errors, failed network
   requests, and cleanup in the run summary.

#### Navigation continuity

1. Start run `rn-0029-navigation-a`. Repeatedly activate Roasts and Beans,
   then use Back and Forward and open a record before returning to its list.
2. At `1440x900`, `1024x768`, and `390x844`, confirm the 56px navbar keeps the
   same geometry, counts and contextual actions stay correct, and the active
   link exposes `aria-current="page"`.
3. With normal motion, confirm main content moves no more than 4px and completes
   in 160-200ms without a second container entrance. Unsupported behavior must
   fall back to an immediate native navigation.
4. Enable reduced motion and repeat Roasts/Beans, Back, and Forward. Confirm
   there is no route fade, translation, or active-indicator choreography.
5. Enter the live-roast shell and verify its chart, readings, setup, sensor
   state, and controls do not receive management content choreography.
6. Verify direct loads and a failed URL remain truthful native document loads.
   Record screenshots, motion observations, history results, console errors,
   failed network requests, and cleanup in the run summary.

### Quiet Compact Settings Sheet

Use run ID `rn-0029-settings-sheet-a`. Start the harness with `--sync-fake`
only when exercising the guarded phase states. Do not perform a live mirror or
either destructive cleanup.

1. At `1440x900`, focus the Settings gear and open it with Enter. Confirm a
   right-aligned sheet no wider than `560px`, no page scroll, initial focus on
   the remembered section tab, and no console error.
2. Use Right Arrow, Left Arrow, Home, and End across Sensor, Data, and Advanced.
   Confirm one selected tab and panel at a time, and confirm hidden panels are
   absent from the Tab order.
3. Tab forward and backward through each visible panel. Confirm focus remains
   inside the sheet. Close with Escape and the close button in separate passes;
   each must return focus to the Settings gear.
4. In Sensor, load and save the URL, test a virtual-sensor success and failure,
   and confirm each visible status is announced. Do not change route payloads.
5. In Data, verify the local E2E label, disabled Online option, ordinary
   fail-closed preflight, then every explicitly simulated backup, apply,
   cancel, restore, terminal, and recovery state from the guarded workflow
   below. Switch sections and close/reopen during a pending or restored state;
   state must not clear, duplicate, or move focus into a hidden panel.
6. In Advanced, confirm Danger Zone starts collapsed. Expand it, cancel both
   existing confirmation paths, and verify no cleanup request is sent.
7. Repeat the shell, focus, section, and overflow checks at `1280x640`,
   `1024x768`, and `390x844`. At mobile width, confirm full-screen layout. In
   short viewports, only the sheet body may scroll while title and tabs remain
   available.
8. Repeat in light and dark modes, then emulate reduced motion and confirm the
   sheet opens without opacity or translation animation.

Save Sensor, Data, expanded-result, Advanced-collapsed, confirmation-cancelled,
short-height, mobile, and dark-mode screenshots. Record focus order and return,
overflow measurements, console errors, failed requests, zero applied-mirror
activity, and cleanup results in the run summary.

#### Browse and Edit Density

Use run ID `rn-0029-management-a` and complete the normal Bean and Roast
workflows below. Repeat the layout checks at `1440x900`, `1280x640`,
`1024x768`, and `390x844` in light and dark modes.

1. Capture Bean and Roast list pages. Verify all existing columns, sorting,
   filtering, row navigation, contextual actions, empty states, and internal
   horizontal scrolling. Confirm the page itself has no horizontal overflow.
2. Create and edit a Bean. Verify labels stay above fields, keyboard focus
   follows the existing source order, every target is at least `44px`, and the
   form becomes one column below `768px`.
3. At the two short-height viewports, scroll through the Bean form and confirm
   Add/Update Bean and Cancel remain reachable. Trigger native required-field
   validation and confirm the invalid field is fully visible above the sticky
   action row.
4. On Beans, verify RN-0027 still shows the exact two-tier Stock cell,
   accessible progressbar, fixed 9% column, raw-value sorting, and narrow-table
   overflow without clipping.
5. Open Bean detail and verify information, pricing, Stock History, flavor,
   notes, and Roast History retain their order and content. Confirm every
   multi-column fact cluster collapses to one column on mobile.
6. Complete Roast edit and detail. Verify field order and payload behavior,
   sticky Save Changes and Cancel, review content, notes, curve, and event data.
   The curve and event tables must keep their existing full-width treatment.
7. Smoke-test the live-roast screen at all four viewports. Record its top bar,
   chart, event controls, sensor states, fullscreen geometry, and target sizes;
   any management layout hook or geometry change is a failure.
8. Record before/after page-height measurements, focus and validation results,
   console errors, failed network requests, screenshots, and cleanup in
   `tests/e2e/artifacts/rn-0029-management-a/summary.md`.

### Guarded Local Settings Sync

First start an ordinary run without `--sync-fake` using run ID
`rn-0028-settings-sync-ordinary`:

1. Open `http://127.0.0.1:5011`, open Settings, and confirm the database label
   contains `local (roastlogger_e2e / rn-0028-settings-sync-ordinary)` and the
   Online radio is disabled.
2. Click **Preview Online → Local**. Confirm the prominent ordinary-E2E error,
   artifact-local preflight audit path, and `503` network response.
3. Confirm `GET /api/sync/runs/active` and direct phase requests return `409`.
   Historic sync URLs also return `409`. No `db_backup/`, online client, or
   non-artifact audit path may be created.
4. Save the fail-closed Settings screenshot and stop the run.

Then start `rn-0028-settings-sync-a` with `--sync-fake`:

1. Open Settings and preview **Online → Local**. Capture the sanitized plan,
   selectable exact `BACKUP <run-id>` token, empty typed field, and enabled
   **Create complete backup** action. Treat raw URI/credential/path data or
   enabled one-click apply as failure.
2. Submit an incorrect first token. Confirm `400`, no backup transition, and
   the instruction to start a fresh preview.
3. Preview again, type the new exact backup token, and submit. Confirm `200`,
   **Complete and verified**, collection/document totals, verified manifest
   SHA-256, backup path, no sync totals, and the empty exact-apply field.
4. Reload the page, reopen Settings, and confirm the same run returns as
   **Restored and re-verified** with preview buttons disabled. Capture this
   apply-gate screenshot.
5. Choose **Cancel run**. Confirm terminal `cancelled_after_backup`, retained
   backup path, applied-audit path, and no sync totals. Capture cancellation.
6. Start a fresh preview. Submit its exact backup token, then its exact
   `APPLY <direction> <run-id>` token. Confirm the terminal per-collection and
   aggregate added/updated/skipped/conflict summary plus applied-audit path.
   Both **Beans outcome** and **Roasts outcome** must be visible. Capture
   success.
7. Verify request URLs/statuses and stage transitions in the network view.
   Repeated backup/apply/cancel requests must return a conflict and must not
   repeat artifacts or results. Treat console errors, failed requests outside
   the deliberate `400`/`409` checks, missing restore state, or any MongoDB
   access as failure.
8. Inspect `sync-fake-events.jsonl`: every event must report
   `database_access: false`; all state, backup, and audit paths must remain
   beneath `tests/e2e/artifacts/rn-0028-settings-sync-a/`.

### Bean

1. Navigate to **Beans**, choose **Add Bean**, and use a run-unique name.
2. Fill origin, process, supplier, purchase date, price, purchase weight,
   stock, flavor notes, notes, and color; save.
3. Confirm the bean appears in inventory and its detail page.
4. Edit several fields and save.
5. Reopen detail and confirm the changes.
6. Open **More actions**, choose **Set stock to zero**, cancel the confirmation,
   and confirm no request was sent and neither stock nor history changed.
7. Repeat and confirm the action. Verify exactly one successful request, a
   `0g` stock display, the exact signed transition at the top of Stock History,
   a success toast, and removal of the now-empty **More actions** menu. Treat
   duplicate requests, console errors, or failed network requests as failures.
8. Return to Beans and confirm the default inventory hides the bean. Enable
   **Show Out of Stock**, reopen it, and confirm the stock history persisted.
9. Edit the bean back to positive stock for the following Live Roast workflow.
   Confirm its history remains and **More actions** is available again.

#### Bean Stock Remaining Meter (Targeted)

1. For run `rn-0027-stock-meter-a`, create or edit the run-marked bean so its
   original purchase weight is `2000g` and its current stock is `300g`.
2. Return to Beans and confirm the Stock cell shows `300g left` in the existing
   pill with a separate thin meter beneath it. Inspect the progressbar and
   confirm its accessible value is 15% with remaining/original context.
3. Confirm the cell shows no visible consumed weight, original-weight fraction,
   or percentage. Sort the Stock column and verify the row follows its raw
   `300g` balance, then open the bean through the clickable row.
4. Capture the Stock cell at desktop and narrow widths in light and dark modes.
   Confirm the 9% column remains aligned, the pill and meter do not clip or
   overlap another column, and narrow layouts retain horizontal scrolling.
5. Treat an incorrect accessible value, visible ratio copy, clipping, column
   overlap, broken horizontal scrolling, console errors, or failed network
   requests as failures. Save both viewport screenshots and the findings in
   `tests/e2e/artifacts/rn-0027-stock-meter-a/summary.md`.

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

Save screenshots for ordinary Settings fail-closed behavior, the permitted
backup gate, restored apply gate, cancelled state, simulated sync success, the
open bean **More actions** menu,
the zero-stock history result, the out-of-stock inventory result, live healthy
state, retry/offline/fault state, and final roast detail. Update `summary.md`
with:

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
