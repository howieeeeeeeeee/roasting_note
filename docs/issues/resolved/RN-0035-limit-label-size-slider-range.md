---
id: RN-0035
title: Limit label size sliders to a practical range
type: improvement
status: resolved
priority: medium
created: 2026-09-16
resolved: 2026-09-16
area: labels
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags: [labels, ui]
---

# Limit label size sliders to a practical range

## Description

Keep label editor text-size controls within the user-requested 70–130% range.

## Details

- The range applies to the interactive sliders only.
- Existing saved values outside this range remain readable through the existing
  API/rendering compatibility path; saving an adjusted slider uses 70–130%.
- No rendering, schema, API, or migration changes are needed.

## Acceptance Criteria

- [x] Every label size slider permits 70–130% and starts at 100%.
- [x] Existing renderer coverage and the slider markup contract pass.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-interaction
- Browser verification level: targeted
- Automated tests to add or update: `tests/test_label_font_size.py`.
- Browser E2E scenarios to add or update: existing Label Creator size-controls scenario in `tests/e2e/README.md`.
- Required commands: `uv run pytest tests/test_label_font_size.py`; `uv run pytest`; `uv run python scripts/generate_issues_index.py`; `uv run python scripts/generate_issues_index.py --check`.
- Required browser evidence: visible slider endpoints and 100% default.
- Not applicable reason: None.

## Documentation Impact

- `docs/design/screens/label-creator.md`
- `docs/features/bean-label-creator.md`
- `tests/README.md` and `tests/e2e/README.md` remain accurate; no change required.

## Resolution

- Set all six interactive sliders to `min=70`, `max=130`, and retained their
  100% default. Existing API and renderer compatibility remains intentionally
  unchanged for previously saved values outside the new editing range.
- `uv run pytest tests/test_label_font_size.py -q` and full `uv run pytest -q`
  passed; tracker generation/check and `git diff --check` passed.
- Browser readback confirmed every slider reports 70–130% with a 100% value.

## Database Operations Impact

- Collections and local/online effects: None; existing saved values remain compatible.
- Migration or backfill: None.
- Expected sync direction: None.
- Is an applied mirror part of delivery: No.
- Required backup/audit evidence for resolution: None.

## Open Questions

- None.

## Related Files

- `templates/beans_detail.html`
- `tests/test_label_font_size.py`
