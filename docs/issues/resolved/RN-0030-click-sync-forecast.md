---
id: RN-0030
title: Simplify Settings Sync and Show Exact Change Forecast
type: improvement
status: resolved
priority: high
created: 2026-08-20
resolved: 2026-08-20
area: database-sync
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - mongodb
  - sync
  - settings
  - safety
  - usability
  - forecast
---

# Simplify Settings Sync and Show Exact Change Forecast

## Description

Make guarded sync in local Settings a clear two-click workflow: create and
verify the complete destination backup, then apply or cancel. Before either
click, show exactly how timestamp-aware synchronization classifies every
in-scope document so the operator knows how many will change and how many will
remain unchanged.

## Details

### Current Behavior

- RN-0028 requires operators to copy and type long run-specific `BACKUP` and
  `APPLY` tokens in Settings even though locality, origin, request shape,
  persisted-run, backup, and replay guards already protect the browser flow.
- The current preview reports only source and destination collection totals.
  Those totals do not reveal which documents are missing, which source copies
  are newer, or which destination documents timestamp-aware sync will retain.
- The guarded CLI intentionally uses exact typed confirmations. Its interface,
  prompt order, statuses, and exit codes remain unchanged by this ticket.
- Configured read-only preflights succeeded on 2026-08-20 in both directions:
  `online-to-local` run `20260820T192814Z-954867bb` and `local-to-online` run
  `20260820T192824Z-c12b05c1`. Neither run created a backup or applied mirror.

### Desired Local Settings Flow

1. Click **Preview Online → Local** or **Preview Local → Online**.
2. Review a sanitized per-collection and aggregate action forecast.
3. Click **Create and verify backup**. The destination backup must complete and
   verify before any apply control appears.
4. Review the verified backup and the same action forecast, then click
   **Apply changes** or **Cancel**.
5. Review the terminal per-collection result and audit or recovery path.

These are two separate guarded actions, not one-click sync. Apply remains
unavailable until the complete destination backup is verified, and cancel
remains available while awaiting apply.

### Exact Action Forecast

Use the same document classifier and active-source scope as the applied sync.
For each requested collection and in aggregate, report:

- documents absent from the destination that will be added;
- matching documents whose source `updated_at` is newer and will be updated;
- matching documents whose destination timestamp is equal or newer and will
  remain unchanged;
- destination-only documents that will remain unchanged;
- matching documents with a missing or incomparable timestamp that will
  remain unchanged and be reported as conflicts;
- total documents that will change, total documents that will remain
  unchanged, and the expected destination count after synchronization.

The response must contain counts only. Do not expose document identifiers, raw
documents, connection URIs, credentials, or topology settings.

The server must recompute and compare the forecast immediately before backup
and again immediately before apply. A changed source or destination forecast
fails closed before that phase performs backup or synchronization writes and
requires the operator to obtain a fresh preview. This preserves a truthful
decision boundary without introducing cross-database locking.

### Safety And Compatibility

- Preserve the direct-peer and Host loopback checks, same-origin JSON request
  requirement, ordinary-E2E exclusion, hosted preview-only behavior, one
  active run, durable awaiting-apply state, replay rejection, complete backup,
  manifest verification, destination identity binding, cancellation, terminal
  audit, recovery evidence, and both sync directions from RN-0028.
- Settings phase requests accept only the server-bound direction. Removing a
  user-entered confirmation string must not add any client-controlled endpoint,
  database, path, collection, run identity, or bypass input.
- Preserve the guarded CLI's two exact typed confirmation tokens and all
  existing CLI behavior.
- Exercise the successful browser flow only through the explicitly injected
  artifact-root E2E fake. No live applied mirror is part of implementation or
  verification.

### Scope Boundaries

- In scope: shared forecast classification, preflight and active-run forecast
  responses, backup/apply revalidation, two-click Settings controls, accessible
  summaries, fake-executor coverage, tests, browser evidence, and documentation.
- Out of scope: one-click sync, remote apply, authentication changes, deletion
  reconciliation, schema or timestamp-policy changes, migration/backfill,
  cross-database locks or transactions, background jobs, and a live mirror.

## Acceptance Criteria

- [x] Eligible local Settings uses one explicit backup button followed by one
  explicit apply button; neither phase requires typing or copying a token.
- [x] Apply remains hidden or disabled until the complete destination backup
  and manifest have been verified, and Cancel remains available before apply.
- [x] Preview and restored awaiting-apply state show per-collection and
  aggregate add, update, unchanged, conflict, change-total, unchanged-total,
  and expected-destination counts using the applied sync classifier.
- [x] Destination-only documents are counted as unchanged, conflicts are
  visibly distinguished from normal unchanged matches, and no identifiers or
  raw database values appear in the forecast.
- [x] Forecast drift before backup causes no backup, applied audit, active run,
  or sync write; drift before apply causes no sync write and retains a
  cancellable recovery-safe active run.
- [x] Loopback, same-origin JSON, ordinary-E2E, hosted, concurrency, replay,
  resume, backup, audit, identity, and recovery guards remain fail closed.
- [x] The guarded CLI retains both exact typed confirmations and its existing
  arguments, prompt order, output, statuses, exit codes, and recovery behavior.
- [x] Both directions work with the injected E2E fake, and no implementation
  or verification step performs a live applied mirror.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: database-sync, backend-api, ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: update `tests/test_database_sync.py` for shared add/update/unchanged/conflict/destination-only classification and aggregate forecast parity; retain `tests/test_sync_api.py` for the applied timestamp behavior; update `tests/test_database_sync_web.py` for forecast persistence, pre-backup and pre-apply drift, resume, failure boundaries, and two-phase click requests; update `tests/test_database_sync_routes.py`, `tests/test_api_contracts.py`, and `tests/test_settings_sheet_contracts.py` for direction-only phase payloads, sanitized forecast responses, button-only controls, and safe DOM rendering; retain `tests/test_database_sync_cli.py` for unchanged typed CLI confirmations; update `tests/test_e2e_runtime.py` and the injected sync fake for deterministic forecast and two-click phase behavior; retain `tests/test_database_backup.py`, `tests/test_app_factory.py`, and `tests/test_file_size_policy.py` in the focused safety suite
- Browser E2E scenarios to add or update: update `tests/e2e/README.md` -> `Guarded local Settings sync`; in ordinary E2E verify apply remains unavailable, then start a separate explicit `--sync-fake` run, preview one direction, verify exact per-collection and aggregate forecast counts, click backup, reload and verify the forecast and awaiting-apply state are restored, cancel, then preview the opposite direction, click backup and apply, and verify the terminal results match the forecast; treat any confirmation text input, premature apply control, raw endpoint data, live database access, production backup access, failed request, or unexpected console error as a failure
- Required commands: `uv run pytest tests/test_database_sync.py tests/test_sync_api.py tests/test_database_sync_web.py tests/test_database_sync_routes.py tests/test_database_sync_cli.py tests/test_database_backup.py tests/test_app_factory.py tests/test_api_contracts.py tests/test_settings_sheet_contracts.py tests/test_e2e_runtime.py tests/test_file_size_policy.py`; `uv run pytest`; `uv run python scripts/sync_database.py --direction online-to-local --dry-run`; `uv run python scripts/sync_database.py --direction local-to-online --dry-run`; `uv run python -m tests.e2e.manage start --run-id rn-0030-sync-summary-ordinary`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0030-sync-summary-ordinary`; `uv run python -m tests.e2e.manage start --run-id rn-0030-sync-summary-a --sync-fake`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0030-sync-summary-a`; `git check-ignore db_backup/database_mirrors/example/state.json`; `git ls-files db_backup 'db_backup/**'`
- Required browser evidence: record both E2E run IDs; save screenshots of ordinary-E2E exclusion, the forecast and first button, restored verified-backup forecast with second button and Cancel, cancellation, and successful terminal summary; record forecast and terminal counts, phase request URLs/statuses, stage transitions, fake events proving zero live database/production-path access, console errors, failed network requests, artifact paths, and cleanup results in the ignored run summaries
- Not applicable reason: None. This changes a critical database workflow, its server contracts, and both pre-backup and pre-write operator decisions.

## Documentation Impact

- Update `docs/features/database-sync.md` with forecast semantics,
  revalidation, the two-click local flow, and retained CLI confirmations.
- Update `docs/design/screens/settings.md` with forecast hierarchy, button
  states, restored state, accessibility, responsive behavior, and errors.
- Update `docs/architecture/api-endpoints.md` with direction-only backup/apply
  payloads and forecast response and conflict contracts.
- Update `docs/audit_history/database_mirrors/README.md` with the sanitized
  plan forecast and drift behavior.
- Update `docs/deployment/README.md` with the simplified local operator flow.
- Update `tests/README.md` with forecast and button-contract coverage.
- Update `tests/e2e/README.md` with the revised full browser scenario and
  required evidence.
- Update project navigation only if implementation adds a new durable document.

## Database Operations Impact

- Collections and local/online effects: preview reads active `beans` and
  `roasts` plus destination documents to classify count-only add, update,
  unchanged, destination-only, and timestamp-conflict outcomes. A later
  separately authorized browser apply retains RN-0015 behavior: it may insert
  missing source documents or replace an older destination copy, and never
  deletes a destination-only document.
- Migration or backfill: None. Document shapes, indexes, and timestamp policy
  remain unchanged.
- Expected sync direction: both `online-to-local` and `local-to-online`.
- Is an applied mirror part of delivery: No. Use configured dry runs, mocks,
  fixtures, isolated state, and the injected browser fake only.
- Required backup/audit evidence for resolution: record both configured dry-run
  IDs, focused/full automated results, full ordinary/fake browser evidence,
  forecast/terminal parity, fake-only paths and cleanup, and an empty
  `git ls-files db_backup 'db_backup/**'`. Do not publish or stage backup state.

## Resolution

- Added one shared timestamp classifier for preview and apply. Preflight now
  reads only `_id` and `updated_at` projections and returns count-only
  per-collection and aggregate additions, newer-source updates, same/newer
  destination matches, destination-only documents, timestamp conflicts,
  change totals, unchanged totals, and expected destination counts.
- Replaced the two Settings text fields with sequential **1. Create and verify
  backup** and **2. Apply _n_ changes** buttons. The compact Outcome ×
  Beans/Roasts/Total matrix keeps every unchanged category visible inside the
  Settings sheet; Apply is absent until the backup verifies, and Cancel remains
  available afterward.
- Added forecast comparison before backup, after backup, on active-run restore,
  and immediately before apply. Pre-backup drift consumes the preview without
  activity; later drift hides Apply and preserves a cancellable active run.
- Kept browser phase payloads direction-only and retained all RN-0028 locality,
  same-origin JSON, state, concurrency, replay, identity, backup, audit, and
  recovery guards. The CLI still uses its two exact typed tokens.
- Focused verification passed with 100 tests. The complete suite passed with
  214 tests, JavaScript syntax validation passed, and `git diff --check` was
  clean.
- Final configured dry runs were read-only and successful:
  `online-to-local` run `20260820T194431Z-8332dd68` forecast 0 changes and 43
  unchanged documents, including 1 destination-only roast; `local-to-online`
  run `20260820T194441Z-89359fdb` forecast 0 changes and 66 unchanged
  documents, including 24 destination-only roasts. Neither run backed up,
  audited, prompted, or wrote either database.
- Full browser evidence used ordinary run `rn-0030-sync-summary-ordinary` and
  artifact-only fake run `rn-0030-sync-summary-a`. Ordinary preflight returned
  `503` and active state `409` with no backup. The fake flow previewed both
  directions, showed 3 changes and 4 unchanged, backed up 6 documents, restored
  after reload, cancelled one run, and applied the other; terminal totals of 2
  added, 1 updated, 2 skipped, and 1 conflict matched the forecast. Replay
  returned `409`, browser console warnings/errors were empty, and every fake
  event reported `database_access: false`.
- Ignored evidence is recorded in
  `tests/e2e/artifacts/rn-0030-sync-summary-ordinary/summary.md` and
  `tests/e2e/artifacts/rn-0030-sync-summary-a/summary.md`, with screenshots,
  request/status logs, fake events, artifact paths, and zero-remaining cleanup.
  `git check-ignore` covered browser and backup state, and
  `git ls-files db_backup 'db_backup/**'` returned no files.
- Updated the database-sync feature, Settings design, API, audit-history,
  deployment, project overview, automated-test inventory, browser runbook, and
  this governing record. No schema change, migration, production path, or live
  applied mirror was used.

## Open Questions

- None. Settings uses two explicit phase buttons with server-side forecast
  revalidation; the CLI keeps its two exact typed tokens.

## Related Files

- `roastlogger/services/database_sync.py`
- `roastlogger/services/database_sync_plan.py`
- `roastlogger/services/database_sync_web.py`
- `roastlogger/blueprints/settings.py`
- `static/js/settings-sheet.js`
- `templates/base.html`
- `tests/e2e/sync_fake.py`
