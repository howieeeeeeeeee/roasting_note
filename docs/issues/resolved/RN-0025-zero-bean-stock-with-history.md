---
id: RN-0025
title: Set Non-Zero Bean Stock to Zero
type: feature
status: resolved
priority: medium
created: 2026-08-20
resolved: 2026-08-20
area: bean-inventory
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - beans
  - inventory
  - stock
  - data-model
---

# Set Non-Zero Bean Stock to Zero

## Description

Let the user set any non-zero bean stock balance to zero from the bean detail
page and retain an embedded, visible history of each change. This supports
discarding remaining beans and correcting negative inventory without archiving
the bean or losing the previous balance.

## Details

- Current behavior: Bean stock can change through manual edits and roast
  operations, but bean detail has no More actions menu, no dedicated set-to-zero
  action, and no stock-change history.
- Desired change: Add **Set stock to zero** to a new bean-detail More actions
  menu whenever the stored integer `stock_grams` is not zero, including when it
  is negative. Keep Create Label, Edit, and Archive in their current locations.
- Confirmation: Show the bean name and signed current balance in the message
  `Set stock from Xg to 0g? This records the change and cannot be undone
  automatically.` Collect no reason or note. Cancellation sends no request and
  changes no data.
- API contract: Add `POST /api/beans/<bean_id>/set-stock-zero`. A successful
  response is HTTP `200` and returns `success`, `previous_stock_grams`,
  `change_grams`, `stock_grams: 0`, and `stock_change` containing the history
  entry with `recorded_at` serialized as an ISO 8601 string. Return
  `{"success": false, "error": "Bean not found"}` with HTTP `404` for a
  missing or archived bean, `{"success": false, "error": "Bean stock is
  already zero"}` with HTTP `409` at zero, and `{"success": false, "error":
  "Bean stock changed; refresh and try again"}` with HTTP `409` when a
  concurrent stock change prevents the conditional update. Preserve the
  existing API-wide HTTP `400` invalid-identifier response.
- Persistence: Add optional `stock_change_log` entries with
  `event_type: "set_to_zero"`, `previous_stock_grams`, `change_grams`,
  `resulting_stock_grams: 0`, and timezone-aware `recorded_at`. Initialize new
  beans with an empty array and treat a missing field on legacy beans as empty;
  no backfill is required.
- Arithmetic: `change_grams` equals `0 - previous_stock_grams`, so a positive
  balance produces a negative change and a negative balance produces a
  positive change.
- Atomicity: Match the active bean and its observed non-zero stock value in the
  update that sets stock to zero, appends exactly one history entry, and writes
  the same timestamp to `updated_at`. A repeated or conflicting request must
  not append a duplicate entry.
- UI result: On success, update Current Stock to `0g`, hide the now-empty More
  actions menu, prepend the new history entry, and show a success toast. On
  failure, leave the visible state unchanged, re-enable the action, and show
  the returned error in a toast.
- History: Render stock-zeroing history newest-first under Stock & Pricing with
  timestamp, previous stock, signed change, and resulting balance. Existing
  history remains after a manual restock and subsequent set-to-zero action.
- Inventory lifecycle: The bean remains unarchived. At zero it is omitted by
  the default Beans filter and remains available through **Show Out of Stock**.
- In scope: Bean-detail interaction, endpoint and route contract, atomic bean
  persistence, embedded history rendering, selected-database behavior,
  timestamp-aware sync compatibility, automated coverage, full Bean browser
  coverage, and the declared documentation.
- Out of scope: Logging manual edits or roast deductions/restorations, automatic
  undo, free-form reasons, preventing negative stock, moving the existing
  Archive control, migration/backfill, and an applied database mirror.
- Verification: Focused API, rendering, route-manifest, sync, and E2E-runtime
  tests; the full pytest suite; the complete Bean browser workflow; configured
  guarded sync dry runs or a recorded environment limitation; and the database
  backup tracked-file check.

The stored entry shape is:

```json
{
  "event_type": "set_to_zero",
  "previous_stock_grams": -25,
  "change_grams": 25,
  "resulting_stock_grams": 0,
  "recorded_at": "Date"
}
```

## Acceptance Criteria

- [x] Bean detail shows **Set stock to zero** in a More actions menu for both
  positive and negative integer stock, and does not show the action at zero.
- [x] The confirmation displays the bean name and signed current balance; a
  cancellation sends no request and changes neither stock nor history.
- [x] A successful request sets stock to zero, records the exact previous
  balance and signed change, updates `updated_at`, and returns the documented
  response.
- [x] The stock update and history append are conditional and atomic; zero,
  repeated, and concurrently stale requests append no duplicate event.
- [x] Missing and archived beans return `404`, while already-zero and
  concurrent-stock conflicts return `409` with stable JSON errors.
- [x] Success updates the stock badge, history, action visibility, and toast;
  failure leaves the page state unchanged and shows an error toast.
- [x] Stock history renders newest-first and survives reload, manual restock,
  another set-to-zero event, and timestamp-aware bean synchronization.
- [x] Zeroed beans remain unarchived, are hidden by the default Beans filter,
  and appear when **Show Out of Stock** is enabled.
- [x] Existing manual-edit and roast stock behavior remains unchanged and does
  not create `stock_change_log` entries.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: backend-api, ui-interaction, cross-workflow, database-sync
- Browser verification level: full
- Automated tests to add or update: `tests/test_beans_api.py` for positive, negative, zero, repeated, missing, archived, concurrent-update, history-ordering, and manual-restock behavior; `tests/test_api_contracts.py` for rendered menu/history states and stable API errors; `tests/test_app_factory.py` for the new route manifest entry; `tests/test_sync_api.py` for `stock_change_log` insert/update round trips; `tests/test_e2e_runtime.py` for run-marker preservation and scoped cleanup after the new mutation
- Browser E2E scenarios to add or update: Update `tests/e2e/README.md` -> `Codex In-App-Browser Workflow` -> `Bean` with a full **Set non-zero stock to zero** scenario: open a non-zero bean detail, open More actions, cancel once and verify no visible or persisted change, confirm once and verify `0g`, the exact newest history row, success toast, and removed action, return to Beans and verify the default filter hides the bean while **Show Out of Stock** reveals it, then reopen detail and verify history persists; treat any unexpected API failure, duplicate event, console error, or failed network request as a failure state
- Required commands: `uv run pytest tests/test_beans_api.py tests/test_api_contracts.py tests/test_app_factory.py tests/test_sync_api.py tests/test_e2e_runtime.py`; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0025-zero-stock-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0025-zero-stock-a`; `uv run python scripts/sync_database.py --direction online-to-local --dry-run`; `uv run python scripts/sync_database.py --direction local-to-online --dry-run`; `git ls-files db_backup 'db_backup/**'`
- Required browser evidence: Record run ID `rn-0025-zero-stock-a`; screenshots of the open More actions menu before mutation, the zero balance with newest history entry after mutation, and the bean revealed by **Show Out of Stock**; record cancel and success assertions, console errors, failed network requests, and cleanup counts in `tests/e2e/artifacts/rn-0025-zero-stock-a/summary.md`
- Not applicable reason: None. This changes a critical inventory-stock interaction and requires full browser verification.

## Documentation Impact

- Create `docs/features/beans-management.md`, which is already linked from the
  feature index but is currently missing, to document bean stock lifecycle,
  zeroing behavior, and history.
- Update `docs/design/screens/bean-inventory.md` for the bean-detail More actions
  menu, confirmation, toast states, and stock-history presentation.
- Update `docs/architecture/data-models.md` for `stock_change_log` and its entry
  fields.
- Update `docs/architecture/api-endpoints.md` for
  `POST /api/beans/<bean_id>/set-stock-zero` and its response/error contract.
- Update `tests/README.md` for the new bean stock-management coverage.
- Update `tests/e2e/README.md` for the full Bean stock-zeroing workflow and
  evidence requirements.

## Database Operations Impact

- Collections and local/online effects: The action mutates only the active bean
  in the currently selected `beans` collection. It sets `stock_grams`, appends
  `stock_change_log`, and refreshes `updated_at`; it does not write `roasts` or
  automatically access the other database role. A later guarded sync copies
  the complete embedded history when this bean is the newer source document.
- Migration or backfill: None. New beans initialize `stock_change_log: []`,
  legacy beans treat a missing field as empty, and the first successful action
  creates the array without a bulk migration.
- Expected sync direction: Either `local-to-online` or `online-to-local`, based
  on which selected database contains the newer bean. Delivery performs no
  automatic synchronization.
- Is an applied mirror part of delivery: No. An applied mirror requires a
  separate explicit user request after preflight and both run-specific
  confirmations.
- Required backup/audit evidence for resolution: Automated verification uses
  fixtures or the isolated E2E database. Before implementation, read
  `docs/features/database-sync.md` and attempt both configured guarded CLI
  dry-run directions, or record unavailable endpoints as an environment
  limitation. At resolution, record that evidence and confirm
  `git ls-files db_backup 'db_backup/**'` returns no tracked files. No applied
  run, backup, or audit record is required or authorized by this ticket.

## Open Questions

- None. The finalized behavior uses the bean-detail menu, visible history, no
  note, and every non-zero integer balance including negative values.

## Resolution

- Added an atomic set-to-zero helper and
  `POST /api/beans/<bean_id>/set-stock-zero` with stable `200`, `404`, and `409`
  contracts. New beans initialize an empty history; legacy beans create it on
  their first successful action.
- Added the non-zero-only bean-detail More actions menu, signed confirmation,
  in-place stock/history/toast updates, newest-first history rendering, and the
  corrected **Show Out of Stock** / **Hide Out of Stock** labels.
- Added positive, negative, zero, repeated, missing, archived, concurrent,
  history-ordering, manual-restock, marker-preservation, rendered-state, route,
  and sync-round-trip coverage across the declared test modules.
- Focused verification passed with 60 tests. The full suite passed with 163
  tests, including tracker and 1,000-line file-size policy checks.
- Full Bean browser verification passed under run ID
  `rn-0025-zero-stock-a`. Cancellation retained `180g` with no request;
  confirmation issued one HTTP `200`, showed the success toast, removed the
  action, and prepended `180g / -180g / 0g`. Reload, default filtering,
  **Show Out of Stock**, manual restock, history retention, and action return
  passed. Console warnings/errors and failed network requests were zero.
  Evidence is recorded in
  `tests/e2e/artifacts/rn-0025-zero-stock-a/summary.md` with the three required
  screenshots. Cleanup deleted one bean and left zero beans and roasts for the
  run.
- Both guarded configured dry runs completed without writes:
  online-to-local `20260820T151628Z-25067fa2` and local-to-online
  `20260820T151643Z-51645688`. No applied mirror, backup, backfill, or migration
  ran.
- Added the Bean Management feature guide and updated bean design, data model,
  API, automated-test, and browser-runbook documentation. Confirmed
  `git ls-files db_backup 'db_backup/**'` and the tracked E2E artifact/runtime
  checks return no files.

## Related Files

- `models/bean_helpers.py`
- `roastlogger/blueprints/beans.py`
- `templates/beans_detail.html`
- `static/css/components/tables.css`
- `tests/test_beans_api.py`
- `tests/e2e/README.md`
