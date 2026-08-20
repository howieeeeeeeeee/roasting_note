# Guarded Database Sync

RoastLogger supports timestamp-aware synchronization between its local and
online MongoDB databases. Applied sync is available through the guarded CLI or
through Settings when the browser reaches the app directly over loopback.
Hosted and non-loopback Settings remain preview-only.

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
- Browser phase routes require a direct loopback peer, a loopback `Host`, JSON
  mutation bodies, and a matching `Origin` whenever one is supplied. Forwarded
  headers never establish locality.

An applied mirror is never an application startup step, automated-test step,
cleanup step, or implicit consequence of changing database mode.

## Settings Guarded Flow

The complete guarded browser flow lives in the Data section of the responsive
[Settings sheet](../design/screens/settings.md). Switching sections or closing
the sheet changes presentation only and never cancels, clears, or advances a
run. Both direction buttons begin with the existing audited, non-mutating
preflight:

```text
POST /api/sync/preflight/online-to-local
POST /api/sync/preflight/local-to-online
```

The response shows a server-generated run ID, sanitized source/destination
roles and host labels, collection counts, complete destination backup scope,
CLI handoff, and audit paths. Both buttons are disabled while the request is
active. Successful and failed preflights each write exactly one
`settings_ui` / `sync_button_clicked` intent event.

On an eligible direct-loopback request, Settings continues as follows:

1. Type the exact `BACKUP <run-id>` value shown by the server.
2. Wait synchronously while every destination collection is backed up and its
   manifest and payload checksums are verified. No sync write occurs.
3. Review the collection/document count, verified manifest SHA-256, ignored
   backup path, and exact `APPLY <direction> <run-id>` value.
4. Apply the timestamp-aware sync or cancel and retain the backup.
5. Review collection/aggregate results and the applied audit or recovery path.

The pre-backup preview capability is process-local and atomically taken by the
first backup attempt. A wrong first token, competing request, application
restart, or worker loss requires a fresh preview and causes no backup or
applied-attempt audit. Once backup begins, an exclusive filesystem claim and
atomic sanitized run state are written under `db_backup/database_mirrors/`.
An awaiting-apply run survives sheet closure, page reload, and application
restart. Only one claimed run may proceed across application processes;
another preview loses cleanly at the claim and cannot overwrite the active run.

Apply and cancel also compete for one exclusive terminal-transition marker.
Concurrent apply/apply or apply/cancel requests can run only one executor and
write only one terminal audit. A marker left by interruption keeps the run
blocked as recovery-required rather than permitting a duplicate action.

Before apply or cancel, the server reconstructs runtime configuration and
checks the saved run ID, direction, endpoint descriptors, credential-free
source and destination topology fingerprints, destination identity, manifest
digest, payload digests, byte counts, and document counts. Corrupt or
interrupted state remains claimed and returns recovery guidance instead of
being retried automatically. Terminal state stays beside its ignored backup;
the active claim is released only after that state is persisted.

The historic one-request mutation URLs remain disabled with HTTP `409`:

```text
POST /api/sync/online-to-local
POST /api/sync/local-to-online
```

They perform no database access, backup, state, or audit write. The supported
loopback-only phase API is:

```text
GET  /api/sync/runs/active
POST /api/sync/runs/<run-id>/backup
POST /api/sync/runs/<run-id>/apply
POST /api/sync/runs/<run-id>/cancel
```

Remote, non-loopback-host, cross-origin, non-JSON, malformed, replayed, and
out-of-order requests fail closed before guarded activity. Host and Origin
parsing rejects user information, queries, fragments, and non-HTTP(S) origins.
Ordinary E2E mode also fails closed. Browser workflow verification injects an
artifact-root-only fake executor; it never constructs an online client, uses a
MongoDB collection, or writes production backup/audit paths.

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

## Shared Applied Operation Sequence

The CLI and Settings adapters call the same backup, apply, and after-backup
cancellation phases. The CLI retains its arguments, output, prompt text/order,
exit codes, backup layout, audits, and recovery guidance:

1. Generate one stable run ID and print or display the complete preflight.
2. Require the exact `BACKUP <run-id>` token.
3. Stream every collection and document in the destination database into an
   Extended JSON backup.
4. Require the exact `APPLY <direction> <run-id>` token.
5. Synchronize selected collections sequentially and stop on first failure.
6. Verify post-run counts and persist one terminal audit record.

A wrong or missing CLI first token leaves no backup and no audit. The Settings
first token is likewise one-use and requires a new preview after mismatch. A
wrong or missing CLI second token retains the completed backup and records
`cancelled_after_backup`; Settings keeps an awaiting-apply run available for an
exact retry or explicit cancel. Backup failure, partial sync failure, audit
recovery, cancellation after backup, and success are terminal.

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
