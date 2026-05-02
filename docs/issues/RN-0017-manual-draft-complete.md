---
id: RN-0017
title: Manually Set Draft Roast to Completed
type: feature
status: resolved
priority: medium
created: 2026-05-02
resolved: 2026-05-02
area: live-roasting
tags:
  - lifecycle
  - draft-roast
---

# Manually Set Draft Roast to Completed

## Description

Users need a way to manually finish a draft roast from the live setup page without running the live roast timer. The app should introduce an explicit roast lifecycle status for new data, while preserving timestamp-derived fallback behaviour for older roasts.

## Details

- Add a draft-only manual action on `/roast/live/<roast_id>` labeled **Set to Completed**.
- Introduce a real roast lifecycle/status field for new and updated roasts:
  - new roast creation sets the lifecycle to draft;
  - starting a roast sets it to started;
  - ending a roast sets it to completed;
  - manually setting a draft to completed sets it to completed.
- Preserve existing roasts by falling back to the current timestamp-derived lifecycle when the explicit status field is missing:
  - `roast_end_time` present -> completed;
  - `roast_start_time` present and no `roast_end_time` -> started/in progress;
  - neither timestamp present -> draft.
- Manual completion is only for draft roasts. It should not be shown for active/started roasts or already completed roasts.
- Manual completion should update lifecycle metadata without fabricating live roast data such as temperature curve points, sensor diagnostics, key timing events, or a Drop event.
- The action should use confirmation copy that makes the lifecycle change clear before the user commits.
- Completed-by-status roasts should appear as completed in dashboard and bean-history lifecycle badges/routes even when they do not have live-roast timing data.
- Old data must remain readable without requiring a one-time migration.

## Acceptance Criteria

- [x] A draft roast on `/roast/live/<roast_id>` exposes a clear **Set to Completed** action.
- [x] Active/started roasts and already completed roasts do not expose the draft-only manual completion action.
- [x] New roast creation writes an explicit draft lifecycle/status value.
- [x] Starting a roast writes the started lifecycle/status value.
- [x] Ending a roast writes the completed lifecycle/status value.
- [x] Manually setting a draft to completed writes the completed lifecycle/status value and refreshes `updated_at`.
- [x] Manual completion does not create temperature curve readings, sensor diagnostics, key timing events, or a Drop event by itself.
- [x] Roasts missing the new lifecycle/status field still derive lifecycle from `roast_start_time` and `roast_end_time` exactly as they do today.
- [x] Dashboard and bean-detail roast history use the explicit lifecycle/status first, with timestamp fallback for old roasts.
- [x] Tests cover new roast status defaults, start/end status transitions, manual draft completion, active-roast rejection, completed-roast rejection, and old-roast fallback.
- [x] Relevant docs updated when implemented: `docs/architecture/data-models.md`, `docs/architecture/api-endpoints.md`, `docs/features/live-roasting.md`, `docs/design/screens/live-roasting.md`.

## Open Questions

- Answered: stored lifecycle values are `draft`, `started`, and `completed`. The UI still labels `started` as **In Progress**.
- Answered: manual draft completion leaves bean stock unchanged. Stock is deducted only by starting a live roast.
- Answered: after manual completion succeeds, the user is redirected to the roast edit page for post-roast fields like roasted weight and notes.
- Answered: manual completion does not require minimum draft fields beyond the roast existing and still being in draft lifecycle.

## Implementation Notes

- New roasts write `lifecycle_status: "draft"`.
- `/api/roast/start/<roast_id>` writes `lifecycle_status: "started"` and rejects non-draft roasts.
- `/api/roast/end/<roast_id>` writes `lifecycle_status: "completed"` and rejects non-started roasts.
- `/api/roast/complete_draft/<roast_id>` is draft-only and only updates `lifecycle_status` plus `updated_at`.
- Dashboard and bean-history badges/routes use `lifecycle_status` first, with timestamp fallback for old documents.

## Related Files

- `app.py`
- `templates/roast_live.html`
- `templates/index.html`
- `templates/beans_detail.html`
- `tests/test_roasts_api.py`
- `docs/architecture/data-models.md`
- `docs/architecture/api-endpoints.md`
- `docs/features/live-roasting.md`
- `docs/design/screens/live-roasting.md`
