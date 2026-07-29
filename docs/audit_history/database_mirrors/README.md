# Database Mirror Audit History

This directory stores reviewable, append-only evidence for guarded database
sync and Settings preflight intent. It never stores raw MongoDB documents,
connection URIs, credentials, session identifiers, IP addresses, backup
payloads, or roast/tasting content.

## Layout

```text
docs/audit_history/database_mirrors/YYYY/MM/
  YYYYMMDDTHHMMSSZ__<DEVICE>__<direction>__<run-id>.json
```

Every filename is unique to one generated run ID. Records are written
atomically and never overwritten.

## Applied Attempt Records

Once the first exact backup confirmation is accepted, one terminal record is
required for:

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

## Settings Intent Records

Every Settings sync-direction button request writes one terminal record with:

- `trigger: settings_ui`;
- `event: sync_button_clicked`;
- device, direction, run ID, and UTC timestamp;
- sanitized endpoint/database descriptors;
- Git provenance when available; and
- successful or failed preflight outcome.

These events prove operator intent and preflight outcome only. They never prove
or initiate an applied sync.

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
