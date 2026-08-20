---
id: RN-0028
title: Enable Guarded Applied Sync in Local Settings
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
  - backup
  - sync
  - audit
  - settings
  - safety
  - loopback
---

# Enable Guarded Applied Sync in Local Settings

## Description

Let a local RoastLogger operator continue from the Settings sync preview into
the same guarded applied workflow currently available only through the CLI.
The browser flow must retain the complete destination backup, two exact typed
confirmations, timestamp-aware merge, redaction, and terminal audit guarantees
from RN-0022 without exposing applied sync on hosted or non-loopback instances.

## Details

### Investigation

- Current behavior is intentional rather than a connectivity or MongoDB
  failure. RN-0022 made Settings preview-only, changed the historic mutation
  routes to fail closed with HTTP `409`, and kept
  `scripts/sync_database.py` as the only applied-sync entry point.
- Configured read-only dry runs succeeded on 2026-08-20 in both directions:
  `online-to-local` run `20260820T155011Z-fea4d432` and
  `local-to-online` run `20260820T155019Z-52d3ab88`. Neither dry run created a
  backup, audit record, prompt, or database write.
- The focused sync suite passed with 23 tests across
  `tests/test_database_sync_routes.py`,
  `tests/test_database_sync_cli.py`, and `tests/test_database_sync.py`.
- The current prompt-driven runner performs backup and apply inside one
  process, so it cannot pause safely between browser requests. It must be
  separated into reusable guarded phases without changing CLI behavior.
- Settings preflight currently writes its intent record to the same planned
  audit filename an applied continuation would use. Browser continuation must
  give intent and applied-attempt records distinct append-only paths while
  retaining one run ID.

### Local Operator Flow

1. The operator clicks **Preview Online → Local** or
   **Preview Local → Online** and reviews the existing sanitized plan.
2. A successful preview on a permitted local instance shows the exact
   `BACKUP <run-id>` token and a typed confirmation field. Preview remains
   non-mutating.
3. Submitting the exact backup token starts a synchronous complete destination
   backup. No synchronization write occurs during this request.
4. After the backup manifest is complete and verified, Settings displays the
   sanitized backup summary and the exact
   `APPLY <direction> <run-id>` token.
5. The operator either submits the exact apply token or cancels. Apply runs
   the timestamp-aware synchronization and displays the per-collection and
   aggregate result plus the audit or recovery path. Cancel retains the
   backup and writes `cancelled_after_backup` terminal evidence.

Closing and reopening Settings or restarting the local application while a
run is awaiting the second confirmation must restore that run. The operator
must apply or cancel it before another browser-applied run can begin.

### Access Boundary

- Applied-sync controls and phase endpoints are available only when the direct
  request peer and request host are both loopback. Do not trust forwarded
  headers to establish locality.
- Browser phase requests use same-origin `application/json`. Reject a supplied
  cross-origin `Origin` and every non-JSON mutation request.
- A remotely served or hosted Settings page may continue to show the read-only
  plan and CLI handoff, but it must not expose enabled browser-apply controls.
  Direct non-loopback phase requests fail closed without backup, audit, state,
  or database writes.
- Ordinary `E2E_MODE` remains fail closed. Successful browser-state coverage
  uses an explicitly injected E2E fake executor that cannot construct an
  online MongoDB client, mutate a database, or write production backup/audit
  paths.
- Remote authentication, authorization, CSRF infrastructure, and enabling
  applied sync on hosted instances are out of scope.

### API And Run State

Keep the historic `POST /api/sync/<direction>` routes disabled. Add these
loopback-only interfaces:

```text
GET  /api/sync/runs/active
POST /api/sync/runs/<run-id>/backup
POST /api/sync/runs/<run-id>/apply
POST /api/sync/runs/<run-id>/cancel
```

- The current preflight response may add sanitized apply eligibility and
  confirmation metadata, but clients must never provide or control endpoint
  URIs, database names, backup paths, or audit paths.
- `backup` accepts only the direction and exact backup confirmation for the
  server-generated run. A missing or incorrect token cancels before backup,
  creates no applied-attempt audit, and requires a fresh preview.
- `apply` accepts only the exact apply confirmation for the prepared run.
  It verifies the persisted phase, direction, run ID, completed backup
  manifest, and destination identity before any collection write.
- `cancel` before backup has no applied-attempt audit. Cancellation after a
  complete backup writes one terminal `cancelled_after_backup` record and
  keeps the backup available for review.
- `active` returns only sanitized nonterminal run state needed to restore the
  Settings UI. It never returns MongoDB URIs, credentials, raw documents, or
  confirmation input.
- Invalid stages, replayed phase requests, a second concurrent run, mismatched
  direction/run identity, incomplete backup evidence, and corrupt state fail
  closed. Duplicate requests must not repeat a backup, sync, or audit write.

Persist atomic sanitized browser-run state under ignored
`db_backup/database_mirrors/` after the first confirmation is accepted. Use a
filesystem-backed exclusive active-run claim so the guard works across
requests and application processes. Preserve terminal state with its backup
for diagnosis; do not stage or publish it. An interrupted or inconsistent run
must remain blocked and expose recovery guidance rather than being silently
discarded or overwritten.

### Shared Guarded Execution

- Refactor the applied runner into explicit backup, apply, and
  after-backup-cancellation phases shared by CLI and Settings adapters.
- Preserve the CLI arguments, printed preflight, prompt order, exact token
  text, cancellation statuses, exit codes, backup layout, audit publication
  guidance, and recovery behavior.
- Preserve RN-0015 merge semantics: insert missing non-archived source
  documents, update only from a newer comparable source, skip a newer/equal
  destination, report timestamp conflicts without overwrite, retain
  destination-only documents, and stop after the first failed collection.
- Each phase runs synchronously. This ticket adds no background job, queue,
  scheduler, polling worker, or new dependency.

### Audit Separation

- Give new Settings preflight intent records a distinct forward-only filename,
  such as an appended `__preflight.json` suffix. Keep the existing applied
  terminal filename as the plan's applied audit path.
- Preserve one run ID across preview, backup, apply/cancel, state, and both
  audit records. The records remain append-only and atomically created.
- Do not rename, rewrite, backfill, or fabricate existing preflight or applied
  audit records.
- Continue writing one terminal applied-attempt record after backup activity
  for success, backup failure, partial sync failure, or cancellation after
  backup. Audit persistence failure retains the existing untracked recovery
  behavior and is prominent in the UI.

### Scope Boundaries

- In scope: both sync directions, the loopback Settings workflow, phased
  execution service, persisted run state, exclusive-run enforcement, audit
  path separation, safe recovery, automated contracts, full browser evidence,
  and synchronized documentation.
- Out of scope: a live applied mirror during implementation or testing,
  one-click sync, confirmation bypasses, remote operation, MongoDB schema or
  timestamp-policy changes, migration/backfill, deletion-based reconciliation,
  background execution, or automatic audit publication.

## Acceptance Criteria

- [x] A successful loopback Settings preflight for either direction shows the
  sanitized plan and an enabled exact `BACKUP <run-id>` confirmation step;
  hosted and non-loopback views remain preview/CLI-only.
- [x] The direct peer, host, same-origin, JSON-content, E2E, and malformed
  request guards fail closed before backup, state, audit, or database access.
- [x] Missing or incorrect first confirmation causes no backup, applied audit,
  sync write, or reusable run, and a fresh preview is required.
- [x] Exact first confirmation backs up the complete destination database and
  verifies its manifest before exposing the second confirmation; it performs
  zero bean or roast synchronization writes.
- [x] Exact `APPLY <direction> <run-id>` is required after backup before either
  collection can be synchronized, with no flag, route, environment value, or
  client payload that bypasses it.
- [x] Cancelling after backup retains the complete backup, performs no sync,
  writes one sanitized `cancelled_after_backup` audit, and releases the active
  run only after terminal state is persisted.
- [x] Successful runs in both directions use RN-0015 timestamp-aware behavior,
  show collection/aggregate outcomes, and write one terminal applied audit.
- [x] Backup failure, partial sync failure, audit persistence failure, corrupt
  state, and interrupted state are credential-free, fail closed, and expose
  the applicable audit or recovery path without fabricating success.
- [x] An awaiting-apply run survives Settings closure, page reload, and
  application restart; no second run or replayed phase can duplicate backup,
  sync, or audit work.
- [x] New Settings intent and applied-attempt records for one run use distinct
  append-only paths, while all existing audit files remain unchanged.
- [x] The guarded CLI retains its existing arguments, output contract, prompt
  order, exact confirmations, exit codes, backup behavior, and audit behavior.
- [x] The E2E success simulation exercises the complete visible workflow using
  only injected fake results and run-scoped ignored artifacts; ordinary E2E
  mode and every automated test remain incapable of a live mirror.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: database-sync, backend-api, ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: add `tests/test_database_sync_web.py` for phased backup/apply/cancel state, atomic persistence, resume, exclusive-run enforcement, replay rejection, manifest validation, and failure recovery; update `tests/test_database_sync_routes.py` for route payloads, loopback peer/host, same-origin JSON, remote and ordinary-E2E exclusion, sanitized responses, and distinct preflight audit paths; update `tests/test_database_sync_cli.py` for CLI compatibility after runner extraction; update `tests/test_database_sync.py`, `tests/test_database_backup.py`, and `tests/test_sync_api.py` where needed to prove both directions, complete backup, zero pre-apply writes, timestamp-aware parity, and partial failure behavior; update `tests/test_app_factory.py` for the public route manifest; update `tests/test_e2e_runtime.py` for fail-closed ordinary E2E and the injected fake-executor boundary; update `tests/test_api_contracts.py` for the Settings phase markup and safe text rendering; retain `tests/test_file_size_policy.py` for every changed source and documentation file
- Browser E2E scenarios to add or update: replace `tests/e2e/README.md` -> `Codex In-App-Browser Workflow` -> `Preflight And Fail-Closed Sync` with a full **Guarded local Settings sync** workflow covering ordinary-E2E exclusion plus an explicitly fake-executor run: preview one direction, submit an incorrect first token and verify no backup transition, obtain a fresh preview, submit the exact backup token, verify the complete-backup summary and absence of sync results, reload Settings and restore the awaiting-apply run, cancel once and verify terminal cancellation, then use a fresh simulated run to submit both exact tokens and verify the terminal collection/aggregate summary; treat enabled controls outside the simulation, duplicate requests, missing recovery state, raw endpoint data, unexpected console errors, failed network requests, or any MongoDB/production backup access as failures
- Required commands: `uv run pytest tests/test_database_sync_web.py tests/test_database_sync_routes.py tests/test_database_sync_cli.py tests/test_database_sync.py tests/test_database_backup.py tests/test_sync_api.py tests/test_app_factory.py tests/test_e2e_runtime.py tests/test_api_contracts.py tests/test_file_size_policy.py`; `uv run pytest`; `uv run python scripts/sync_database.py --direction online-to-local --dry-run`; `uv run python scripts/sync_database.py --direction local-to-online --dry-run`; `uv run python -m tests.e2e.manage start --run-id rn-0028-settings-sync-ordinary`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0028-settings-sync-ordinary`; `uv run python -m tests.e2e.manage start --run-id rn-0028-settings-sync-a --sync-fake`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0028-settings-sync-a`; `git check-ignore db_backup/database_mirrors/example/state.json`; `git ls-files db_backup 'db_backup/**'`
- Required browser evidence: record ordinary run ID `rn-0028-settings-sync-ordinary` and fake-executor run ID `rn-0028-settings-sync-a`; save screenshots of ordinary-E2E exclusion, the permitted preflight/backup gate, verified-backup/apply gate after reload, cancelled state, and successful simulated terminal summary; record request URLs/statuses, exact stage transitions, zero live database/production-backup access, audit/state artifact paths, console errors, failed network requests, and cleanup results in the matching ignored artifact summaries
- Not applicable reason: None. Settings and database sync are critical surfaces, and this change spans preview, backup, resume, cancellation, apply, and recovery stages.

## Documentation Impact

- Update `README.md` so the supported applied entry points include guarded
  local Settings as well as the CLI, while hosted Settings remains preview-only.
- Update `docs/README.md` to remove the statement that applied sync is isolated
  exclusively in the CLI and describe the local guarded adapter.
- Update `docs/features/database-sync.md` with the local browser lifecycle,
  access boundary, phase transitions, persisted state, CLI parity, failure
  recovery, and explicit exclusion of hosted apply.
- Update `docs/design/screens/settings.md` with the backup/apply typed gates,
  active, waiting, restored, cancelled, success, failure, accessibility, and
  responsive states.
- Update `docs/architecture/api-endpoints.md` with the active-run and phased
  mutation endpoints, request/response contracts, locality checks, stage
  conflicts, and retained legacy-route behavior.
- Update `docs/audit_history/database_mirrors/README.md` with distinct
  preflight/applied filenames, same-run correlation, terminal event rules,
  persisted state boundaries, and forward-only compatibility.
- Update `docs/deployment/README.md` with the local-only Settings operator flow
  and explicit hosted-instance exclusion.
- Update `tests/README.md` with the phased web-sync test inventory, fake
  executor boundary, focused commands, and no-live-mirror guarantee.
- Update `tests/e2e/README.md` with the full guarded local Settings scenario,
  required safe simulation, evidence, and cleanup.
- Conditional: update `docs/architecture/tech-stack.md` only if implementation
  introduces a new runtime setting, dependency, or execution component beyond
  the planned dependency-injected E2E fake.

## Database Operations Impact

- Collections and local/online effects: `beans` and `roasts` remain the
  default timestamp-aware synchronization scope in both directions. A later
  operator-authorized run reads the source, backs up every destination
  collection, and may insert or update destination beans/roasts only after the
  second exact confirmation. It never deletes destination-only documents.
- Migration or backfill: None. RN-0015 timestamps and document shapes are
  unchanged, and browser run state is an ignored operational artifact rather
  than MongoDB data.
- Expected sync direction: both `online-to-local` and `local-to-online`.
- Is an applied mirror part of delivery: No. Delivery implements the guarded
  capability and verifies it with fakes, fixtures, isolated local state, and
  configured CLI dry runs only. A live mirror requires a later separate
  operator request after its visible preflight and both exact run-specific
  confirmations.
- Required backup/audit evidence for resolution: record both configured CLI
  dry-run results or their environment limitations; record focused/full test
  and full browser fake-executor evidence; verify preflight/applied audit paths
  cannot collide; verify representative state/backup content is ignored; and
  confirm `git ls-files db_backup 'db_backup/**'` returns no files. If a live
  mirror is separately authorized outside this ticket, additionally record
  its run ID, reviewed audit path, and manual publication outcome without
  tracking its backup.

## Open Questions

- None. Browser apply is loopback-only, retains the two exact typed gates in
  backup-then-apply order, runs each phase synchronously, and leaves hosted
  operation and live-mirror verification out of scope.

## Resolution

Implemented a loopback-only Settings continuation that shares the CLI's
guarded backup, apply, and cancellation phases. The four phase routes require
direct loopback peer and host checks; mutations additionally require JSON and
same-origin requests. A one-use preview capability precedes an atomic ignored
run claim, complete verified backup, persisted awaiting-apply state, and one
exclusive apply-or-cancel transition. Restart verification now binds both
endpoints and the backup manifest to credential-free scheme/host/topology
fingerprints before any write. Hosted, remote, legacy mutation, and ordinary
E2E paths remain fail closed.

Verification completed on 2026-08-20:

- The declared focused suite passed `95` tests, and `uv run pytest` passed all
  `196` tests. Coverage includes both directions, exact tokens, zero writes
  before apply, resume, endpoint-configuration drift, corruption, replay,
  concurrency, audit recovery, inherited-fake isolation, CLI compatibility,
  markup/focus behavior, and the file-size policy.
- Configured CLI dry run `20260820T164331Z-4ae16898` completed
  online-to-local, and `20260820T164337Z-da6e4d37` completed
  local-to-online. Both commands used `--dry-run`; neither prompted, created a
  backup or audit, nor performed a database write.
- Ordinary browser run `rn-0028-settings-sync-ordinary` returned `409` for
  active-state lookup and `503` for the audited preflight, exposed no
  confirmation control, logged no console warning/error, and cleaned to zero
  remaining beans and roasts. Evidence is in the ignored run summary and
  `screenshots/ordinary-e2e-exclusion.png`.
- Fake-only browser run `rn-0028-settings-sync-a` covered an incorrect first
  token, a fresh exact backup, reload/restoration, cancellation, the opposite
  direction, visible incorrect APPLY rejection, and exact terminal apply.
  Screenshots record the backup gate, restored apply gate, cancelled state,
  and successful collection/aggregate summary. Expected wrong-token requests
  returned `400`; all valid phase requests returned `200`; console
  warning/error output was empty.
- The fake log contains exactly three preflights, two backups, and one
  synchronize event, all with `database_access: false`. Every fake backup,
  state, audit, and screenshot stayed under its ignored artifact root; saved
  state contains no MongoDB URI or credential string. Cleanup left zero beans,
  roasts, and temp logs.
- `git check-ignore db_backup/database_mirrors/example/state.json` confirmed
  the operational-state boundary, `git ls-files db_backup 'db_backup/**'`
  returned no files, and the configured dry runs left no production
  `db_backup/` directory.

No live or applied database mirror was run. Any future applied mirror remains
a separate explicit operator action requiring its visible preflight and both
run-specific confirmations.

## Related Files

- `roastlogger/blueprints/settings.py`
- `roastlogger/services/database_sync_runner.py`
- `roastlogger/services/database_sync_ui.py`
- `roastlogger/services/database_sync_audit.py`
- `roastlogger/services/database_sync_plan.py`
- `templates/base.html`
- `static/css/components/modals.css`
- `scripts/sync_database.py`
- `tests/test_database_sync_routes.py`
- `tests/test_database_sync_cli.py`
- `tests/e2e/README.md`

## Related Records

- `RN-0022` established the complete-backup, exact-confirmation, redaction,
  audit, and CLI contracts this ticket must preserve. It explicitly deferred
  a future guarded browser-applied workflow to separate work.
- `RN-0015` defines the timestamp-aware insert, update, skip, conflict, and
  destination-retention behavior shared by both applied entry points.
