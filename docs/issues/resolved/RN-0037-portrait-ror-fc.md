---
id: RN-0037
title: Keep End Roast steady on portrait iPads and show the latest FC marker
type: bug
status: resolved
priority: medium
created: 2026-11-19
resolved: 2026-11-19
area: live-roasting
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags: [live-roasting, chart, tablet]
---

# Keep End Roast steady on portrait iPads and show the latest FC marker

RoR crossing 10.0 can move End Roast to a second row during a roast. Recording
First Crack Start again resets the development timer but leaves the old line on
the chart. Operators need a steady control and one marker at the corrected time.

## Acceptance Criteria

- [x] End Roast stays in place as RoR alternates between 9.9 and 10.0 on portrait iPads, before and after FC.
- [x] Only the last saved First Crack Start appears on the live, reloaded live, edit and detail charts. Other event types and the underlying event log are preserved.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-interaction
- Browser verification level: full
- Automated tests to add or update: `tests/test_live_roast_ui.py` and its Node regression checks for live, restored and historical annotations.
- Browser E2E scenarios to add or update: Live Roast in `tests/e2e/README.md`, including portrait readings and recording FC twice through completion.
- Required commands: `uv run pytest tests/test_live_roast_ui.py`, `uv run pytest`, and `uv run python scripts/generate_issues_index.py --check`.
- Required browser evidence: Run ID, button geometry around 10.0, live/reload/history marker results, screenshots, console/network findings and run-scoped cleanup.
- Not applicable reason: None.

## Documentation Impact

- `docs/design/screens/live-roasting.md` for portrait layout.
- `docs/features/live-roasting.md` and `docs/features/chart-visualization.md` for FC corrections.
- `tests/README.md` and `tests/e2e/README.md` for regression coverage.

## Database Operations Impact

None. Both changes affect presentation of existing readings and recorded events.

## Resolution

Portrait readings reserve space for a signed RoR and fit beside End Roast.
One shared annotation rule moves the FC line to its latest recorded time in
the live, resumed, edit and detail charts.

- Focused Node-backed regressions passed. Full pytest passed all 252 tests on
  the isolated `roastlogger_test_rn0037` database.
- Browser run `rn-0037-portrait-a` checked 744, 768, 810, 820, 834, 1024 and
  1032 CSS pixels, before and after FC in normal and fullscreen. End Roast had
  identical bounds at 9.9, 10.0, 9.9 and −10.0 at each width and in each mode.
- Live and resumed charts moved FC from 00:44 to 00:54. A fullscreen correction
  at 03:06 survived reload, ending and saving. Both history charts showed one
  FC at 03:06, alongside Yellowing, FC End and Drop. The Data tab retained all
  three FC presses.
- The ignored run directory contains `geometry.json`, `markers.json`,
  screenshots, service logs and `summary.md`. App console and HTTP checks
  passed. The virtual sensor recovered after the injected failures. Scoped
  cleanup removed two roasts, one bean and four CSVs with zero records remaining.
