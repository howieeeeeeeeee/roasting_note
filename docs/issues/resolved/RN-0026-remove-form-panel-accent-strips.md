---
id: RN-0026
title: Remove Form Panel Accent Strips
type: improvement
status: resolved
priority: low
created: 2026-08-20
resolved: 2026-08-20
area: design-system
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - design
  - forms
  - css
  - visual
---

# Remove Form Panel Accent Strips

## Description

Remove the decorative color strip from the left edge of shared form panels so
Bean and Roast editing surfaces use the quieter neutral panel treatment already
established elsewhere in RoastLogger.

## Details

- Current behavior: `.form-section::before` draws a 3px primary-color strip
  along the full left edge of every `.form-section`, including Bean Profile,
  Flavor Notes, Inventory, and Roast edit panels. The strip is decorative and
  makes ordinary data-entry groups read as emphasized status surfaces.
- Desired change: Remove that pseudo-element strip without replacing it with a
  colored edge, glow, inset bar, or other ornament. Retain hierarchy through
  the existing neutral border, low shadow, section-heading divider, spacing,
  and typography.
- Minimal cleanup: Remove `position` or overflow declarations only if focused
  review confirms they became unused when the pseudo-element is removed. Do
  not otherwise recalibrate panel dimensions or tokens.
- In scope: The shared `.form-section` style in light and dark modes, including
  its use by Bean add/edit and Roast edit forms, plus the matching reusable-form
  design documentation.
- Out of scope: Toast severity borders, timeline status indicators, bean color
  dots, input focus rings, buttons, field layout, card radius/shadow changes,
  interactions, content, APIs, and database behavior.
- Verification: Review the focused CSS diff, confirm the shared templates still
  use the unchanged `.form-section` structure, run the file-size policy test,
  and run the full pytest suite.

## Acceptance Criteria

- [x] `.form-section` panels render with no primary, bean-defined, or other
  colored strip along the left edge in both light and dark modes.
- [x] Bean add/edit and Roast edit panels retain their neutral background,
  border, radius, low shadow, heading divider, padding, and responsive layout.
- [x] No replacement accent ornament is added, and semantic color treatments
  for toasts, timelines, focus states, and bean identity remain unchanged.
- [x] Form fields, actions, accessibility states, and application behavior are
  unchanged.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-visual
- Browser verification level: none
- Automated tests to add or update: None. The change removes one decorative CSS pseudo-element and does not alter markup, layout, interaction, or behavior.
- Browser E2E scenarios to add or update: None
- Required commands: `uv run pytest tests/test_file_size_policy.py`; `uv run pytest`; `git diff --check`
- Required browser evidence: None
- Not applicable reason: This is a small, low-risk cosmetic removal that preserves the shared panel box model, content, responsive layout, and every interaction contract.

## Documentation Impact

- Update `docs/design/components/forms.md` to remove the left-accent rule from
  the canonical `.form-section` description and state that form panels use a
  neutral edge.

## Database Operations Impact

None. Focused reads confirm this ticket changes only shared CSS presentation and
its design documentation. It performs no collection write, schema change,
migration, backfill, synchronization, backup, or audit operation.

## Open Questions

- None. The minimal direction is a neutral form panel with no decorative left
  color strip; semantic color cues elsewhere remain intact.

## Resolution

- Removed only the `.form-section::before` rule that drew the 3px primary-color
  strip. No replacement edge, glow, inset, or ornament was added.
- Retained the shared panel background, neutral border, radius, padding, low
  shadow, positioning, overflow, heading divider, transitions, and responsive
  padding. Bean add/edit and Roast edit templates keep their existing
  `.form-section` structure with no markup or behavior changes.
- Updated `docs/design/components/forms.md` so the canonical component guidance
  specifies neutral edges in light and dark modes.
- Verification passed: `git diff --check`, the focused file-size policy test
  (`1 passed`), and the complete pytest suite (`163 passed`). Browser evidence
  remains not applicable under the declared `none` level because the change is
  a small visual-only pseudo-element removal that preserves layout and every
  interaction contract.
- Database operations remain not applicable; no schema, data, sync, backup, or
  audit behavior changed.

## Related Files

- `static/css/components/forms.css`
- `docs/design/components/forms.md`
- `templates/beans_form.html`
- `templates/roast_edit.html`
