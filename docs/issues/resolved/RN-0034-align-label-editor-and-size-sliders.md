---
id: RN-0034
title: Align label editor and replace font inputs with sliders
type: improvement
status: resolved
priority: high
created: 2026-09-16
resolved: 2026-09-16
area: labels
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags: [labels, ui, accessibility]
---

# Align label editor and replace font inputs with sliders

## Description

Make the label editor more spacious and aligned by grouping its per-field text
sizes into a dedicated slider panel.

## Details

- Replace the six inline number inputs with accessible 50–200% range sliders,
  a visible value, and a 100% default that preserves existing rendering.
- Give label content controls more vertical room and align the slider rows,
  including the longest label, at desktop and narrow widths.
- Preserve saved per-field text scales, previews, exports, and API behavior.

## Acceptance Criteria

- [x] Label content controls and text-size controls have clear spacing and aligned rows.
- [x] Each text field has a live 50–200% slider and value; 100% remains the saved-default behavior.
- [x] Existing saved font sizes, preview rendering, and exports retain their behavior.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-visual, ui-interaction
- Browser verification level: targeted
- Automated tests to add or update: `tests/test_label_font_size.py` and `tests/label_font_size_check.cjs`.
- Browser E2E scenarios to add or update: targeted Label Creator slider check in `tests/e2e/README.md`.
- Required commands: `uv run pytest tests/test_label_font_size.py`; `uv run pytest`; `uv run python scripts/generate_issues_index.py`; `uv run python scripts/generate_issues_index.py --check`.
- Required browser evidence: desktop modal screenshot, slider value/readout and live preview update; narrow-width overflow check.
- Not applicable reason: None.

## Documentation Impact

- `docs/design/screens/label-creator.md`
- `docs/features/bean-label-creator.md`
- `tests/README.md` and `tests/e2e/README.md`

## Resolution

- Replaced the cramped per-field number inputs with one lightly surfaced Text
  size panel. Each row has a labelled slider and percentage readout; controls
  remain independently adjustable and save only non-default values.
- Increased label content control height and spacing, aligned slider labels,
  and kept the responsive panel to one column below the modal breakpoint.
- `uv run pytest tests/test_label_font_size.py -q` passed **2 tests**; the Node
  canvas renderer check and `git diff --check` passed. Full `uv run pytest -q`
  passed **251 tests**.
- Targeted browser verification opened the existing label editor without saving
  user data. Name changed from 100% to 125% and immediately updated its readout
  and canvas. At the requested narrow 390px browser viewport (487 CSS pixels at
  the browser's 80% zoom), the page and modal had no horizontal overflow.
- Updated the feature/design docs, automated-test inventory, and durable browser
  checklist. No API, data-shape, migration, or database operation changed.

## Database Operations Impact

- Collections and local/online effects: None; existing optional label size values retain their current persistence.
- Migration or backfill: None.
- Expected sync direction: None.
- Is an applied mirror part of delivery: No.
- Required backup/audit evidence for resolution: None.

## Open Questions

- None.

## Related Files

- `templates/beans_detail.html`
- `static/css/screens/label-creator.css`
- `static/js/label-creator.js`
