---
id: RN-0022
title: Add Guarded, Audited Bidirectional Database Sync
type: improvement
status: resolved
priority: high
created: 2026-07-29
resolved: 2026-07-29
area: database-sync
parent:
decisions: []
blocked_by: []
tags:
  - mongodb
  - backup
  - sync
  - audit
  - cli
  - device
  - safety
---

# Add Guarded, Audited Bidirectional Database Sync

## Description

Replace unguarded operational database-sync writes with a maintained,
device-attributed workflow modeled on
`econ_experiment_agents` ticket `EEA-0012`. The workflow must preview the
operation, back up the complete destination, require two exact confirmations,
preserve RoastLogger's timestamp-aware merge rules, and record each applied
attempt in an append-only audit history.

The guarded CLI is the primary applied-sync entry point. The Settings modal
retains direction buttons as audited, non-mutating preflight actions, while the
existing sync API routes must no longer provide a way to bypass the backup,
confirmation, and audit guarantees.

## Details

### Current Behavior

- The Settings modal immediately calls `POST /api/sync/online-to-local` or
  `POST /api/sync/local-to-online`.
- The endpoints synchronize the `beans` and `roasts` collections directly.
  They preserve the timestamp-aware conflict behavior delivered by `RN-0015`,
  but they do not provide a dry run, create a destination backup, attribute the
  run to a device, require typed confirmations, or write an audit record.
- `.env.example` documents the database endpoints but not the stable machine
  identity needed to distinguish local backup origins and audit records.
- The operator's untracked `.env` already uses
  `DEVICE=howie-macbook-air`. That local value must remain untracked and must
  not be copied into application logs or committed configuration.

### Proposed Operator Flow

Add `scripts/sync_database.py` as the supported operational entry point:

```bash
# Preview online -> local
uv run python scripts/sync_database.py \
  --direction online-to-local \
  --dry-run

# Apply online -> local with two confirmations
uv run python scripts/sync_database.py \
  --direction online-to-local

# Preview local -> online
uv run python scripts/sync_database.py \
  --direction local-to-online \
  --dry-run

# Apply local -> online with two confirmations
uv run python scripts/sync_database.py \
  --direction local-to-online

# Restrict sync scope; the complete destination is still backed up
uv run python scripts/sync_database.py \
  --direction online-to-local \
  --collection beans
```

The CLI must support:

- required `--direction {online-to-local,local-to-online}`;
- repeatable `--collection`, limited to known source collections and defaulting
  to `beans` and `roasts`;
- a positive `--batch-size`; and
- `--dry-run`.

Use the existing endpoint names and database name:

| Direction | Source | Destination | Required destination backup |
| --- | --- | --- | --- |
| `online-to-local` | `MONGO_URI` / `roastlogger` | `MONGO_URI_LOCAL` / `roastlogger` | Complete local database |
| `local-to-online` | `MONGO_URI_LOCAL` / `roastlogger` | `MONGO_URI` / `roastlogger` | Complete online database |

Reject a missing or blank `DEVICE`, unsafe device/path characters, an invalid
batch size, unknown collections, unavailable endpoints, and configurations
whose source and destination resolve to the same endpoint and database.
Console output and audit records may show only sanitized roles, host labels,
database names, and the stable device name; they must never expose a MongoDB
URI or credentials.

### Timestamp-Aware Sync Contract

Move the existing synchronization behavior behind focused, reusable services
so the CLI and any retained route adapter cannot drift:

- Synchronize non-archived source documents from `beans` and `roasts`.
- Insert a source document when its `_id` is absent from the destination.
- Update an existing destination document only when both `updated_at` values
  are valid and the source is newer.
- Skip a destination document that is newer than or equal to the source.
- Report a conflict, without overwriting, when timestamps cannot be compared.
- Preserve the source timestamps for copied documents and keep the existing
  legacy-timestamp fill behavior for new destination documents.
- Retain destination-only documents; synchronization must never delete data.
- Process collections sequentially and stop on the first failed collection.

This ticket adds operational safeguards around the behavior from `RN-0015`; it
does not replace it with unconditional `_id` upserts.

### Dry Run And Applied Run

A dry run must check connectivity and print the complete plan: run ID, device,
direction, sanitized endpoints, resolved sync collections, source and
destination counts, full destination-backup scope and path, and planned audit
path. It must not create a backup, prompt for confirmation, write an audit
record, or write to either database.

An applied run must:

1. Generate a stable run ID and print the complete preflight plan.
2. Require the exact token `BACKUP <run-id>`. A mismatch or end-of-input
   cancels before backup work and creates no audit record.
3. Back up the complete destination database. Abort before sync if any
   collection or manifest step is incomplete.
4. Require the exact token `APPLY <direction> <run-id>`. There is no `--yes`,
   environment flag, or other confirmation bypass.
5. Synchronize resolved collections sequentially and stop on the first
   failure.
6. Print per-collection and aggregate added, updated, skipped, conflict, and
   post-run count summaries.

No synchronization write may occur before both exact tokens have been
accepted. Backup filesystem writes happen after the first token and before the
second by design.

### Restorable Destination Backup

Every applied run must back up every collection and document in the destination
database, including archived documents and collections excluded by
`--collection`.

- Preserve `_id`, BSON dates, `ObjectId`, `Decimal128`, nested values, and other
  supported BSON values using documented MongoDB Extended JSON.
- Stream one document per line to an encoded per-collection `.jsonl` file
  without loading a full collection into memory.
- Record the source collection name and use collision-safe reversible
  filenames.
- Record document counts, byte sizes, and SHA-256 checksums.
- Write collection files and the manifest atomically.
- Build under a clearly named partial directory and finalize only after every
  destination collection succeeds.
- Retain incomplete backups for diagnosis, with sanitized failure metadata,
  without allowing them to look restorable.

Use ignored, origin-specific paths under the repository-root `db_backup/`
directory:

```text
db_backup/database_mirrors/local--<DEVICE>/roastlogger/
  <UTC timestamp>__<run-id>/
db_backup/database_mirrors/online/roastlogger/
  <UTC timestamp>__<run-id>/
```

The completed manifest must include a schema version, Extended JSON mode, run
ID, backup reason, destination role and database name, initiating device, UTC
timestamps, completion status, collection entries with filenames/counts/bytes/
checksums, and aggregate collection/document counts. Backup payloads and
manifests must remain ignored and must never be staged or committed.

### Append-Only Audit History

Document the audit contract at
`docs/audit_history/database_mirrors/README.md` and write one atomic JSON record
per applied attempt at:

```text
docs/audit_history/database_mirrors/YYYY/MM/
  YYYYMMDDTHHMMSSZ__<DEVICE>__<direction>__<run-id>.json
```

Each record must include:

- schema version, run ID, status, UTC start/end timestamps, and duration;
- `DEVICE`, direction, sanitized source/destination descriptors, and database
  names;
- timestamp-aware mode, batch size, requested/resolved collections, and
  preflight counts;
- destination-backup path, manifest SHA-256, completion state, and counts;
- per-collection added, updated, skipped, conflict, and post-run counts;
- post-run verification and aggregate totals;
- sanitized failure or cancellation details; and
- the Git commit, branch, and dirty-worktree state of the code that performed
  the operation.

Create an applied-attempt audit record for success, backup failure after the
first confirmation, partial sync failure, and cancellation after backup. CLI
dry runs and CLI cancellation before backup starts do not create an
applied-attempt record.

Every Settings-modal sync direction button click is an explicit audit event,
even though the button is non-mutating. Write a separate terminal UI-intent
record containing `trigger: settings_ui`, `event: sync_button_clicked`, the
direction, `DEVICE`, run ID, UTC timestamp, sanitized endpoint/database
descriptors, Git provenance when available, and the preflight outcome. Record
both successful and failed preflight outcomes, including sanitized failures.
Do not include raw session identifiers, IP addresses, credentials, MongoDB
URIs, raw documents, tasting/roast content, or backup payloads.

If the tracked audit write fails after backup or database activity, write the
same sanitized record into the untracked backup directory, exit nonzero, and
print the recovery path prominently. The CLI must never stage, commit, or push;
after a tracked record is written it prints Git commands scoped to that one
record.

Do not fabricate historical audit records for existing UI syncs because their
device, backup, confirmation, and timing evidence is unavailable.

### Settings Modal And API Safety

Applied sync is CLI-only in this ticket. Keep the Settings modal's two
direction buttons, but change them into audited, non-mutating preflight
actions:

1. A click requests a server-generated run ID and sanitized plan for the chosen
   direction.
2. The backend writes one `sync_button_clicked` UI-intent audit record with the
   preflight outcome.
3. The modal displays source/destination roles, collection counts, backup
   scope, the required CLI command, and any sanitized preflight error.
4. The click must not create a backup, prompt for apply confirmation, or write
   to either database.

Disable repeated clicks while the preflight request is active and restore both
button states after completion. Display audit-record failure prominently; the
UI must not report a fully recorded preflight when the record was not
persisted.

Replace or repurpose the existing mutating POST routes. Any route retained at
the old URLs must fail closed with migration guidance and perform no backup,
audit, or database writes. A dedicated read-only preflight route may serve the
new button behavior.

A future browser-applied workflow may be proposed separately, but it must use
the same complete-backup, two-confirmation, sync, redaction, and audit services.
It must not reintroduce a one-click sync or another shortcut around the guarded
flow.

### Environment Example

Update `.env.example` with a required but intentionally blank device field and
a commented example:

```dotenv
# Required for applied database sync. Use a unique, stable value per machine.
# Example: DEVICE=howie-macbook-air
DEVICE=
```

The blank default prevents cloned environments from silently sharing one
device identity. Applied sync must reject the blank value.

### Standard Agent Workflow For Database Work

Make the guarded database workflow part of the repository's durable agent and
ticket policies. This policy applies when a ticket changes a MongoDB document
shape, persistence behavior, database route/service, migration/backfill,
database configuration, or synchronization behavior.

Update `AGENTS.md`, `CLAUDE.md`, the ticket-master skill and workflow, and the
active ticket template to require the following:

1. A new or refined database-impacting ticket includes a
   `## Database Operations Impact` section. It identifies affected
   collections, local/online effects, migration or backfill needs, expected
   sync direction, whether an applied mirror is part of delivery, and the
   backup/audit evidence required for resolution. Use `None` only after focused
   repository reads establish that no live database operation is needed.
2. Before implementing database-impacting work, the agent reads
   `docs/features/database-sync.md` and runs the guarded CLI in `--dry-run`
   mode when configured endpoints are available. An unavailable endpoint is
   reported as an environment limitation; it is a blocker only when the ticket
   requires live-data evidence.
3. Implementation and automated verification use mocks, fixtures, or an
   isolated local database. An applied online/local mirror is never an implicit
   test, startup step, cleanup step, or ordinary consequence of selecting a
   database ticket.
4. An applied mirror requires a separate, explicit user request after the
   preflight plan is visible, followed by both run-specific confirmation
   tokens. Agents must not infer approval, automate input, add a bypass, or
   reuse consent from an earlier run.
5. After an applied mirror, the operator reviews the result and manually
   publishes only the generated audit record. Backup contents and manifests
   stay under ignored `db_backup/` and are never staged.
6. Before resolving a database-impacting ticket, record the dry-run result or
   applied run ID/audit path in `## Resolution`, verify the required docs, and
   confirm that `git ls-files db_backup 'db_backup/**'` returns no files.

The ticket-master skill remains planning and tracker maintenance only. It adds
the database-operations requirements to relevant records and verifies the
recorded evidence at resolution; it must not perform an applied database sync
during a ticketing turn.

Add `/db_backup/` to `.gitignore`. Verification must cover both
`git check-ignore db_backup/...` and an empty tracked-file query so an existing
file cannot remain tracked merely because a later ignore rule was added.

## Acceptance Criteria

- [x] `scripts/sync_database.py` supports both directions, repeatable
  collection filters, a positive batch size, and dry-run mode.
- [x] Missing/blank/unsafe `DEVICE`, same endpoint/database identities, invalid
  batch sizes, unavailable endpoints, and unknown requested collections fail
  safely with credential-free messages.
- [x] Dry run checks connectivity and prints the complete plan without backup
  writes, audit writes, prompts, or database writes.
- [x] Applied runs require exact `BACKUP <run-id>` and
  `APPLY <direction> <run-id>` tokens, with no bypass and no sync write before
  both tokens.
- [x] Both directions preserve `RN-0015` timestamp-aware insert, update, skip,
  conflict, timestamp, archived-source, and destination-only retention rules.
- [x] Resolved collections run sequentially and processing stops on the first
  failure.
- [x] Every applied run backs up the complete destination database before the
  second confirmation, regardless of collection filters.
- [x] Backups stream Extended JSON Lines, preserve tested BSON types, use
  atomic partial/final paths, and include restorable manifests with counts,
  byte sizes, and SHA-256 checksums.
- [x] Backup paths under `db_backup/database_mirrors/` distinguish
  `local--<DEVICE>` from `online` and are never included in commits.
- [x] `.gitignore` contains a repository-root `/db_backup/` rule,
  `git check-ignore` recognizes representative backup content, and
  `git ls-files db_backup 'db_backup/**'` returns no tracked files.
- [x] Successful, backup-failed, partially failed, and
  cancelled-after-backup applied attempts create one atomic, sanitized audit
  JSON record; CLI dry runs and CLI pre-backup cancellations create no
  applied-attempt record.
- [x] Every Settings sync-button click creates one atomic, sanitized
  `sync_button_clicked` UI-intent audit record with trigger, direction, device,
  run ID, time, Git provenance, and successful or failed preflight outcome.
- [x] Audit-write failure retains the same sanitized record inside the
  untracked backup and exits with a visible recovery message.
- [x] The CLI never stages, commits, or pushes and prints publication commands
  scoped to only the new audit record.
- [x] The Settings modal buttons run audited read-only preflight, show the
  sanitized plan and CLI handoff, prevent overlapping clicks, and never create
  a backup or database write.
- [x] Existing mutating sync routes cannot perform an unguarded database write;
  any retained old route fails closed with CLI migration guidance.
- [x] `.env.example` includes the required blank `DEVICE` setting, explains
  stable per-machine naming, and shows `howie-macbook-air` only as a comment.
- [x] `AGENTS.md` and `CLAUDE.md` define the standard database-ticket workflow:
  read-only dry run by default, isolated automated tests, and separately
  authorized applied mirrors with both run-specific confirmations.
- [x] `.claude/skills/ticket-master/SKILL.md`,
  `.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md`, and
  `.agents/skills/ticket-master/SKILL.md` require database-impacting tickets to
  record database operations, backup/audit evidence, and resolution
  verification without performing application work during ticketing.
- [x] `docs/issues/templates/TICKET.md` contains a conditional
  `## Database Operations Impact` prompt, and tracker tests protect the
  database-workflow guidance and template contract.
- [x] Automated tests cover preflight validation, both directions, dry-run
  side effects, both confirmations, timestamp-aware sync parity, complete
  destination backups, BSON round trips, checksums, audit event policy,
  redaction, one-record-per-button-click behavior, overlapping-click
  prevention, UI/API fail-closed behavior, and partial failures.
- [x] Focused database-sync tests and `uv run pytest` pass without making an
  applied live-database write.
- [x] A configured live check, if performed, is read-only via `--dry-run`; an
  applied run requires a separate deliberate human operation.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Documentation Impact

- `README.md`
- `docs/features/database-sync.md`
- `docs/architecture/api-endpoints.md`
- `docs/architecture/tech-stack.md`
- `docs/deployment/README.md`
- `tests/README.md`
- `docs/audit_history/database_mirrors/README.md`
- `docs/design/screens/settings.md`
- `docs/design/README.md`
- `docs/README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.agents/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md`
- `docs/issues/templates/TICKET.md`
- Conditional: `docs/architecture/data-models.md` if implementation changes the
  timestamp or document-shape contract instead of preserving `RN-0015`.

## Database Operations Impact

- Collections: `beans` and `roasts` are the default synchronization scope; an
  applied run also reads and backs up every collection in the destination
  database.
- Local/online effects: the implementation changes synchronization,
  preflight, backup, audit, configuration, and route behavior for both local
  and online database roles.
- Migration/backfill: none. The `RN-0015` timestamp and document-shape
  contract is preserved.
- Expected synchronization direction: both `online-to-local` and
  `local-to-online` are supported, but no applied mirror is part of this
  delivery.
- Verification: automated work uses isolated fakes/fixtures. Configured live
  checks are read-only `--dry-run` preflights. Resolution requires dry-run
  evidence, full test results, documentation updates, and confirmation that
  `db_backup/` has no tracked files.
- Applied backup/audit evidence: not applicable unless the user separately
  authorizes a run after seeing its preflight and supplies both run-specific
  confirmation tokens. The current authorization explicitly excludes an
  applied run.

## Resolution

- Delivered the guarded services and CLI in `d11e43a`, regression coverage in
  `0496d9e`, and synchronized operator/design/policy documentation in
  `13469c3`.
- Preserved RN-0015 timestamp-aware behavior, added complete canonical Extended
  JSON destination backups, two exact confirmations, append-only terminal
  audits, and untracked audit recovery.
- Changed Settings sync actions to audited read-only preflight and retained the
  historic mutation routes as fail-closed HTTP `409` adapters.
- Configured read-only dry runs succeeded for both directions:
  `online-to-local` run `20260729T072720Z-6ea086e9` and `local-to-online` run
  `20260729T072742Z-5c829fed`. Neither run created a backup, prompt, audit, or
  database write.
- Focused sync/tracker/line-policy verification passed with 53 tests. The
  required `uv run pytest` completed with 131 tests passing.
- `git check-ignore` recognizes representative destination-backup content,
  `git ls-files db_backup 'db_backup/**'` returns no files, and `.env` remains
  ignored and uncommitted.
- Updated every unconditional Documentation Impact path. The conditional data
  model document was not changed because RN-0015 timestamp and document shapes
  remain unchanged.
- No applied mirror was requested or performed, so no applied run ID, backup,
  or applied-attempt audit exists.

## Open Questions

- None. The proposed first implementation uses a guarded CLI for applied sync
  and audited Settings buttons for read-only preflight. A browser-applied
  workflow can be ticketed separately if command-line operation proves
  inconvenient.

## Related Files

- `app.py`
- `scripts/sync_database.py`
- `.env.example`
- `.gitignore`
- `AGENTS.md`
- `CLAUDE.md`
- `.agents/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md`
- `docs/issues/templates/TICKET.md`
- `templates/base.html`
- `static/css/components/modals.css`
- `tests/test_ticket_system.py`
- `tests/test_sync_api.py`
- `tests/test_database_sync.py`
- `tests/test_database_backup.py`
- `tests/test_database_sync_cli.py`
- `docs/audit_history/database_mirrors/README.md`
- `docs/features/database-sync.md`
- `docs/architecture/api-endpoints.md`
- `docs/architecture/tech-stack.md`
- `docs/deployment/README.md`
- `docs/design/screens/settings.md`
- `docs/design/README.md`
- `README.md`

## Related Records

- `RN-0015` defines the timestamp-aware merge behavior that this ticket must
  preserve.
- `RN-0018` provides the application factory, blueprint, configuration, and
  service boundaries used by this ticket. RN-0022 starts only after RN-0018 is
  resolved.
