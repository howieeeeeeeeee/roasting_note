# Guarded Database Sync

RoastLogger supports timestamp-aware synchronization between its local and
online MongoDB databases. Settings is preview-only. The guarded CLI is the only
supported applied-sync entry point.

## Safety Contract

- `DEVICE` is a required stable machine identifier.
- Dry runs read connectivity, collection names, and document counts only.
- Applied runs back up the complete destination database before any sync.
- Applied runs require exact `BACKUP <run-id>` and
  `APPLY <direction> <run-id>` tokens, with no bypass.
- Every applied attempt after backup starts produces a terminal audit record.
- Backup payloads stay under ignored `db_backup/`; reviewed audit records live
  under `docs/audit_history/database_mirrors/`.
- Console, API, and audit output never includes MongoDB URIs or credentials.

An applied mirror is never an application startup step, automated-test step,
cleanup step, or implicit consequence of changing database mode.

## Settings Preflight

The Settings modal keeps both direction buttons as audited, non-mutating
preflight actions. A click calls:

```text
POST /api/sync/preflight/online-to-local
POST /api/sync/preflight/local-to-online
```

The response shows a server-generated run ID, sanitized source/destination
roles and host labels, requested collection counts, complete destination backup
scope, CLI handoff, and audit path. Both buttons are disabled while the request
is active. Successful and failed preflights each write exactly one
`settings_ui` / `sync_button_clicked` audit event.

The historic mutation URLs remain only to fail closed with HTTP `409` and CLI
migration guidance:

```text
POST /api/sync/online-to-local
POST /api/sync/local-to-online
```

They perform no database access, backup, or audit write.

The interaction and visual states are specified in
[Settings screen design](../design/screens/settings.md).

## CLI Usage

Preview both directions:

```bash
uv run python scripts/sync_database.py \
  --direction online-to-local \
  --dry-run

uv run python scripts/sync_database.py \
  --direction local-to-online \
  --dry-run
```

Applied operation, only after separate authorization:

```bash
uv run python scripts/sync_database.py \
  --direction online-to-local
```

The CLI accepts repeatable `--collection beans|roasts`, defaults to both known
collections, and accepts a positive `--batch-size`. Collection filters change
the synchronization scope but never reduce the complete destination backup.
Dry run never prompts, creates a backup, writes an audit, or changes either
database.

Preflight rejects:

- blank or path-unsafe `DEVICE`;
- missing endpoints;
- source and destination resolving to the same host and database;
- unavailable endpoints;
- unknown collections; and
- non-positive batch sizes.

Failures are credential-free. Endpoint descriptions contain only roles, host
labels, and database names.

## Applied Operation Sequence

1. Generate one stable run ID and print the complete preflight.
2. Require the exact `BACKUP <run-id>` token.
3. Stream every collection and document in the destination database into an
   Extended JSON backup.
4. Require the exact `APPLY <direction> <run-id>` token.
5. Synchronize selected collections sequentially and stop on first failure.
6. Verify post-run counts and persist one terminal audit record.

A wrong or missing first token leaves no backup and no audit. A wrong or
missing second token retains the completed backup and records
`cancelled_after_backup`. Backup failure, partial sync failure, and success are
also audited.

## Timestamp-Aware Merge

The service preserves the RN-0015 behavior for non-archived source documents:

- insert when `_id` is absent at the destination;
- update only when both `updated_at` values are valid and source is newer;
- skip when destination is newer or equal;
- report a conflict without overwrite when timestamps cannot be compared;
- preserve source timestamps, filling legacy missing timestamps on the copied
  destination document; and
- retain all destination-only documents.

Per-collection and aggregate output includes added, updated, skipped, conflict,
and post-run counts.

## Destination Backup

Every applied attempt backs up all destination collections, including archived
documents and collections outside the selected sync scope. Each collection is
written as canonical MongoDB Extended JSON, one document per line, using a
collision-safe reversible filename. The manifest records collection names,
counts, byte sizes, SHA-256 checksums, aggregate counts, destination role,
database, device, run ID, timestamps, and completion state.

Backups build in a `.partial` directory. Only a fully written collection set
and manifest is renamed to the final path:

```text
db_backup/database_mirrors/local--<DEVICE>/roastlogger/
  <timestamp>__<run-id>/
db_backup/database_mirrors/online/roastlogger/
  <timestamp>__<run-id>/
```

Incomplete backups retain sanitized failure metadata but no completed
manifest, so they cannot be mistaken for restorable output.

## Audit Publication

See [Database mirror audit history](../audit_history/database_mirrors/README.md)
for the record schema and publication procedure. The CLI never stages, commits,
or pushes. It prints Git commands scoped to the single generated record.

If tracked audit persistence fails after backup or database activity, the CLI
writes the same sanitized record as `audit-recovery.json` under the untracked
backup and exits nonzero with the recovery path.
