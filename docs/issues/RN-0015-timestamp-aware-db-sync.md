---
id: RN-0015
title: Make Database Sync Timestamp-Aware
type: bug
status: resolved
priority: high
created: 2026-05-01
resolved: 2026-05-02
area: database-sync
tags:
  - sync
  - database
  - data-integrity
---

# Make Database Sync Timestamp-Aware

## Description

The Settings modal can already run Local -> Online and Online -> Local database sync, but the current backend sync replaces matching target documents without checking whether the target copy is newer. Make both sync directions safe for beans and roasts by comparing `updated_at` timestamps before overwriting target documents.

## Details

- Current behaviour: `sync_collection(source_col, target_col)` copies every non-archived source document and calls `replace_one()` for matching `_id` values, even when the target document may be newer.
- Desired behaviour: during Local -> Online sync, insert missing online beans/roasts, but only overwrite an existing online bean/roast when the online `updated_at` is older than the local document's `updated_at`.
- Desired behaviour: during Online -> Local sync, insert missing local beans/roasts, but only overwrite an existing local bean/roast when the local `updated_at` is older than the online document's `updated_at`.
- When a bean or roast is actually copied to the target database, the implementation should preserve/update timestamp semantics consistently so future sync decisions are based on reliable `updated_at` values.
- Sync results should report enough information for the Settings modal/operator to understand what happened: added, updated, skipped because target was newer/equal, and any records that could not be compared.
- The flow should remain operable through the Settings modal's existing **Local -> Online** and **Online -> Local** buttons, and it should also be safe for an agent/operator to trigger either endpoint intentionally.

## Acceptance Criteria

- [x] Local -> Online sync inserts local beans and roasts that do not exist online.
- [x] Local -> Online sync overwrites an existing online bean/roast only when the online `updated_at` is older than the local `updated_at`.
- [x] Local -> Online sync skips existing online beans/roasts when the online `updated_at` is newer than or equal to the local `updated_at`.
- [x] Online -> Local sync inserts online beans and roasts that do not exist locally.
- [x] Online -> Local sync overwrites an existing local bean/roast only when the local `updated_at` is older than the online `updated_at`.
- [x] Online -> Local sync skips existing local beans/roasts when the local `updated_at` is newer than or equal to the online `updated_at`.
- [x] Sync responses include skipped/conflict counts in addition to added/updated counts.
- [x] Missing or invalid `updated_at` values are handled explicitly and do not cause silent data loss.
- [x] Tests cover older target, newer target, equal timestamp, missing target document, and missing timestamp cases for beans and roasts.
- [x] Relevant docs updated when implemented: `docs/architecture/api-endpoints.md`, `docs/architecture/data-models.md`, and the database sync feature documentation (`docs/features/database-sync.md` if created, otherwise `docs/features/README.md`).

## Open Questions

- Answered: timestamp-aware comparison applies to both Local -> Online and Online -> Local sync.
- Answered: when the source document is copied to the target, the target keeps the source `updated_at`; sync time is not written as `updated_at`.
- Answered: when either existing side has no valid `updated_at`, sync skips the overwrite, increments `conflicts`, and reports the document id in `conflict_ids`.
- Answered: archived documents continue to be ignored by sync.

## Implementation Notes

- `sync_collection()` now returns `added`, `updated`, `skipped`, `conflicts`, and `conflict_ids`.
- Existing target documents are replaced only when both `updated_at` values are valid datetimes and the source timestamp is newer.
- Missing target documents are still inserted, with missing `created_at` or `updated_at` values filled on the copied target document.
- The Settings modal completion toast now reports skipped and conflict counts.

## Related Files

- `app.py`
- `templates/base.html`
- `tests/test_sync_api.py`
- `docs/architecture/api-endpoints.md`
- `docs/architecture/data-models.md`
- `docs/features/database-sync.md`
