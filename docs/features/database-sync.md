# Database Sync

Local and online database switching and sync from the Settings modal.

## Overview

RoastLogger keeps two MongoDB connections:

- **Local**: `MONGO_URI_LOCAL`, selected by default for the site.
- **Online**: `MONGO_URI`, used when explicitly selected or as a sync target/source.

The Settings modal exposes a Local / Online selector and two sync actions:

- **Online -> Local**: `POST /api/sync/online-to-local`
- **Local -> Online**: `POST /api/sync/local-to-online`

## Default Mode

The application defaults to local mode. `DEFAULT_DB` can still be configured,
but invalid values fall back to `local`, and Render is configured with
`DEFAULT_DB=local`.

## Timestamp-Aware Sync

Sync copies non-archived beans and roasts from the selected source collection to
the target collection.

For each source document:

- If the target document does not exist, sync inserts it.
- If both source and target have valid `updated_at` timestamps and the source is newer, sync replaces the target.
- If the target timestamp is newer than or equal to the source timestamp, sync skips the document.
- If either side is missing `updated_at` or has an invalid timestamp, sync reports a conflict and does not overwrite the target.

`updated_at` is preserved from the source document when a document is inserted or
updated. This keeps future sync comparisons tied to the actual last edit time
instead of the sync time. When sync inserts a legacy source document that is
missing `created_at` or `updated_at`, it fills the missing timestamp fields on
the copied target document.

## Response Counts

Each sync response returns counts for beans and roasts:

```json
{
  "success": true,
  "beans": {
    "added": 1,
    "updated": 2,
    "skipped": 3,
    "conflicts": 0,
    "conflict_ids": []
  },
  "roasts": {
    "added": 0,
    "updated": 1,
    "skipped": 4,
    "conflicts": 1,
    "conflict_ids": ["6653f2a4e5a8f6c75159a111"]
  }
}
```

The Settings modal includes skipped and conflict counts in its completion toast
so the operator can tell whether sync copied data or left newer/incomparable
target records untouched.
