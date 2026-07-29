---
id: RN-0009
title: Draft Roast Opens As Read-Only Detail Page
type: bug
status: resolved
priority: high
created: 2026-04-24
resolved: 2026-04-24
area: live-roasting
parent:
decisions: []
blocked_by: []
tags:
  - dashboard
  - lifecycle
  - autosave
---

# Draft Roast Opens As Read-Only Detail Page

## Description

When a user creates a new roast, enters setup information, leaves for the dashboard, and then opens that roast again, the app shows the read-only roast detail experience instead of the live roast setup experience. The user can no longer start the roast or see the live roast curve from that path, so the draft roast feels like it has been treated as a completed roast.

## Reproduction

1. Click **Start New Roast** from the dashboard.
2. On `/roast/live/<roast_id>`, enter draft setup information such as roast name, bean, green weight, ambient temperature, or humidity.
3. Leave the live roast page without clicking **Start Roast**.
4. Return to the dashboard.
5. Click the roast name or the view action for the draft roast.

## Actual Behavior

- The dashboard links the roast to `/roast/detail/<roast_id>`.
- The detail page is read-only and oriented around viewing completed roast data.
- There is no obvious way to resume the draft on `/roast/live/<roast_id>`.
- Any setup values that are only stored client-side before **Start Roast** may be lost, except fields that have their own autosave behavior.

## Expected Behavior

- A roast with no `roast_start_time` and no `roast_end_time` should still be treated as a draft/pre-start roast.
- Opening a draft from the dashboard should take the user back to `/roast/live/<roast_id>` so they can continue setup and click **Start Roast**.
- The UI should clearly distinguish draft, active, and completed roasts.
- Setup information entered before starting should either persist immediately or the UI should make it clear that it has not been saved yet.

## Investigation Notes

- `roast_new()` creates a draft roast and redirects to the live route.
- The live page decides whether to show the active setup/start/chart UI based on `not roast.roast_end_time`, so an unended draft can still render the live UI if loaded through `/roast/live/<roast_id>`.
- The dashboard currently links every roast name and view action to `roast_detail`, regardless of lifecycle state.
- The detail page is documented and designed as a read-only view for completed roasts, so routing drafts there creates the "finished roast page" feeling.
- The live setup form only autosaves the roast title on blur; bean, green weight, ambient temperature, and humidity are sent to the server when **Start Roast** is clicked.

## Likely Root Cause

The app does not model roast lifecycle state explicitly in navigation. Dashboard links treat all roasts as detail-viewable records, even when a roast is still a draft. Separately, pre-start setup fields are not persisted before the start action, so leaving the live page before starting can discard setup edits.

## Proposed Fix

- Add lifecycle-aware dashboard links:
  - Draft roast: no `roast_start_time` and no `roast_end_time` -> link to `/roast/live/<roast_id>` and label action as **Resume Setup**.
  - Active roast: has `roast_start_time` and no `roast_end_time` -> link to `/roast/live/<roast_id>` and label action as **Resume Roast**.
  - Completed roast: has `roast_end_time` -> link to `/roast/detail/<roast_id>` and label action as **View**.
- Consider adding a status badge on the dashboard: `Draft`, `In Progress`, `Completed`.
- Persist setup fields before start, either with an explicit **Save Setup** action or autosave for bean, green weight, ambient temperature, and humidity.
- Add regression coverage for dashboard routing by roast lifecycle state.

## Acceptance Criteria

- [x] A draft roast opened from the dashboard returns to the live setup page and still shows **Start Roast**.
- [x] An active roast opened from the dashboard returns to the live roast page and shows the running controls.
- [x] A completed roast opened from the dashboard still opens the detail page.
- [x] The dashboard makes the roast state visible enough that a draft does not look completed.
- [x] Setup fields entered before starting are not silently lost, or the UI explicitly communicates when they are unsaved.

## Resolution

- Added lifecycle metadata for roast list rendering so draft and active roasts link back to `/roast/live/<roast_id>`, while completed roasts continue to link to `/roast/detail/<roast_id>`.
- Added status badges for `Draft`, `In Progress`, and `Completed` in the dashboard and bean roast history.
- Added `/api/roast/update_setup/<roast_id>` so pre-start setup fields autosave without starting the roast or decrementing bean stock.
- Updated live-roast reload behavior so an already-started roast resumes with **End Roast** and event controls enabled.
- Fixed draft deletion so it does not restore bean stock that was never deducted.
- Added regression tests for lifecycle routing, setup autosave, started-roast setup rejection, and draft deletion stock behavior.

## Related Files

- `app.py`
- `templates/index.html`
- `templates/beans_detail.html`
- `templates/roast_live.html`
- `templates/roast_detail.html`
- `tests/test_roasts_api.py`
