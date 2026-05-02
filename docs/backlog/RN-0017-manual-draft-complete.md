---
id: RN-0017
title: Manually Set Draft Roast to Completed
type: feature
status: pending
priority: medium
created: 2026-05-02
resolved:
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

- [ ] A draft roast on `/roast/live/<roast_id>` exposes a clear **Set to Completed** action.
- [ ] Active/started roasts and already completed roasts do not expose the draft-only manual completion action.
- [ ] New roast creation writes an explicit draft lifecycle/status value.
- [ ] Starting a roast writes the started lifecycle/status value.
- [ ] Ending a roast writes the completed lifecycle/status value.
- [ ] Manually setting a draft to completed writes the completed lifecycle/status value and refreshes `updated_at`.
- [ ] Manual completion does not create temperature curve readings, sensor diagnostics, key timing events, or a Drop event by itself.
- [ ] Roasts missing the new lifecycle/status field still derive lifecycle from `roast_start_time` and `roast_end_time` exactly as they do today.
- [ ] Dashboard and bean-detail roast history use the explicit lifecycle/status first, with timestamp fallback for old roasts.
- [ ] Tests cover new roast status defaults, start/end status transitions, manual draft completion, active-roast rejection, completed-roast rejection, and old-roast fallback.
- [ ] Relevant docs updated when implemented: `docs/architecture/data-models.md`, `docs/architecture/api-endpoints.md`, `docs/features/live-roasting.md`, `docs/design/screens/live-roasting.md`.

## Open Questions

- Should the stored lifecycle values be exactly `draft`, `started`, and `completed`, or should the middle value be `active` / `in_progress` to match current UI language?
- When a draft is manually set to completed, should bean stock be decremented based on `original_weight_grams`, left unchanged, or handled through a confirmation choice?
- After manual completion succeeds, should the user stay on the live setup page, redirect to the roast detail page, or redirect to the roast edit page for post-roast fields like roasted weight and notes?
- Should manual completion require any minimum draft fields, such as bean, green weight, or roast date?

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
