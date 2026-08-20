# Database Mirror Audit History

This directory stores reviewable, append-only evidence for guarded database
sync and Settings preflight intent. It never stores raw MongoDB documents,
connection URIs, credentials, session identifiers, IP addresses, backup
payloads, or roast/tasting content.

## Layout

```text
docs/audit_history/database_mirrors/YYYY/MM/
  YYYYMMDDTHHMMSSZ__<DEVICE>__<direction>__<run-id>.json
  YYYYMMDDTHHMMSSZ__<DEVICE>__<direction>__<run-id>__preflight.json
```

The unsuffixed path is reserved for the terminal applied attempt. New Settings
intent records use `__preflight.json`, allowing the same server-generated run
ID to correlate preview and a later browser-applied attempt without a filename
collision. Records are atomically created and never overwritten.

This naming rule is forward-only. Existing unsuffixed Settings intent records
are valid historical evidence and are not renamed, rewritten, backfilled, or
treated as applied attempts.

## Applied Attempt Records

Once the CLI accepts its exact backup token, or Settings accepts its explicit
backup-phase click, one terminal record is required for:

- `success`;
- `backup_failed`;
- `partial_sync_failed`; or
- `cancelled_after_backup`.

Cancellation before backup and dry run create no applied-attempt record.
Applied records include run/device/direction identity, timestamps and duration,
sanitized endpoint/database descriptors, timestamp-aware mode, batch and
collection scope, preflight counts, complete destination-backup evidence,
per-collection and aggregate results, post-run verification, sanitized
failure/cancellation details, and Git commit/branch/dirty state.

New preflight data also includes the sanitized action forecast: per-collection
and aggregate add, update, unchanged, destination-only, timestamp-conflict,
change-total, unchanged-total, and expected-after counts. It contains no
document identifier or raw document. The applied attempt keeps that reviewed
forecast so an operator can compare it with terminal results.

## Settings Intent Records

Every Settings sync-direction button request writes one terminal record with:

- `trigger: settings_ui`;
- `event: sync_button_clicked`;
- device, direction, run ID, and UTC timestamp;
- sanitized endpoint/database descriptors;
- Git provenance when available; and
- successful or failed preflight outcome.

These events prove operator intent and preflight outcome only. An eligible
loopback response may create a process-local, one-use capability for the first
Settings backup click, but the tracked intent record itself cannot initiate an
applied sync.

## Browser Run State

Browser continuation stores sanitized operational state and one exclusive
active claim under ignored `db_backup/database_mirrors/`, never in this tracked
history. State contains run/direction identity, sanitized endpoint descriptors,
credential-free source and destination topology fingerprints,
the forecasted plan, backup evidence, phase, and in-progress terminal record;
it contains no URI, credential, raw document, identifier, or confirmation
input.

No applied-attempt record exists before a valid Settings backup click or exact
CLI backup confirmation. Settings recomputes its count-only forecast before
backup and apply; a pre-backup mismatch creates no applied record, while a
post-backup mismatch leaves the run available only for cancellation. After
backup activity, Settings uses the same terminal event policy as the CLI: success,
backup failure, partial sync failure, or cancellation after backup produces one
unsuffixed applied record. Audit-write failure preserves the sanitized record
as ignored `audit-recovery.json` and exposes that path instead of claiming
publication success.

## Review And Publication

The CLI prints commands scoped to the newly written record but does not run
Git. Before publication:

1. Inspect the JSON for the expected run ID and sanitized content.
2. Confirm the related backup remains under ignored `db_backup/`.
3. Stage only the reviewed audit JSON.
4. Confirm `git diff --cached --name-only` contains no backup or environment
   files.

If tracked audit persistence fails after backup or database activity, the CLI
exits nonzero and writes `audit-recovery.json` under the untracked backup path.
Review and manually copy only the sanitized recovery record into this history;
never move backup payloads or manifests here.
