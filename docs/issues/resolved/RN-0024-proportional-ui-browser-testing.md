---
id: RN-0024
title: Make UI Browser Testing Proportional
type: improvement
status: resolved
priority: medium
created: 2026-07-29
resolved: 2026-07-29
area: testing
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - ticket-system
  - testing
  - ui
---

# Make UI Browser Testing Proportional

## Description

Scale browser verification to UI change risk so small visual fixes do not
require a full browser workflow while interaction and critical workflow changes
retain appropriate regression coverage.

## Details

- Current behavior: Ticket policy requires every visible UI change, including
  small visual-only fixes, to add and run a browser scenario.
- Desired change: Define `none`, `targeted`, and `full` browser verification
  levels, select them proportionally, and ask the user one concise question
  during ticket creation only when the correct level is materially ambiguous.
- In scope: Ticket-master guidance, testing workflow, templates, tracker
  validation, generated tracker wording, repository guidance, test runbooks,
  and focused policy tests.
- Out of scope: Product UI changes, new browser tooling, and CI browser
  execution.
- Verification: Focused tracker tests, deterministic tracker generation, the
  generated-output stale check, file-size policy, and the full pytest suite.

## Acceptance Criteria

- [x] Small visual-only fixes may declare browser level `none` with a concrete
  reason and are not forced through a full browser task.
- [x] Focused interaction changes use `targeted` browser verification, while
  critical or cross-workflow changes use `full` verification.
- [x] Ticket-master asks one concise level-selection question only when risk or
  reach makes the choice materially unclear.
- [x] UI interaction classifications still fail validation when browser
  scenarios or evidence are omitted.
- [x] Ticket templates and canonical test guidance explain how to record the
  proportional browser level without duplicating scenario inventories.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: backend-api, documentation-only
- Browser verification level: none
- Automated tests to add or update: `tests/test_ticket_system.py`
- Browser E2E scenarios to add or update: None
- Required commands: `uv run pytest tests/test_ticket_system.py`; `uv run python scripts/generate_issues_index.py`; `uv run python scripts/generate_issues_index.py --check`; `uv run pytest`
- Required browser evidence: None
- Not applicable reason: This changes ticket policy and validation only; it does not change the RoastLogger product UI.

## Documentation Impact

- `.agents/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/TESTING_WORKFLOW.md`
- `.claude/skills/ticket-master/templates/TICKET.md`
- `docs/issues/templates/TICKET.md`
- `docs/issues/resolved/RN-0023-testing-impact-workflow.md`
- `docs/issues/README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `tests/README.md`
- `tests/e2e/README.md`

## Database Operations Impact

None. Focused repository reads confirmed this ticket changes only tracker
policy, validation, templates, and documentation. It performs no database
operation, migration, sync, backup, or audit action.

## Open Questions

- None.

## Resolution

- Added explicit `none`, `targeted`, and `full` browser verification levels to
  ticket-master, the testing workflow, both ticket templates, and repository
  guidance.
- Allowed small low-risk visual-only fixes to omit browser work with a concrete
  reason, while retaining targeted coverage for interactions and full coverage
  for cross-workflow and release classifications.
- Directed ticket-master to ask one concise question with a recommendation only
  when focused reads leave the appropriate level materially unclear.
- Updated tracker validation and focused policy tests for permitted visual
  omissions, required interaction scenarios, and full cross-workflow coverage.
- Verification passed: 14 focused tracker tests, deterministic generator,
  generated-output check, and 153 full-suite tests.
- Browser evidence was not applicable because this ticket changed policy and
  validation, not the RoastLogger product UI.
- Confirmed `.env` remains ignored and no database backup, E2E data, or browser
  artifact is tracked.

## Related Files

- `.claude/skills/ticket-master/TESTING_WORKFLOW.md`
- `.claude/skills/ticket-master/scripts/tracker/validation.py`
- `.claude/skills/ticket-master/scripts/tracker/rendering.py`
- `docs/issues/templates/TICKET.md`
- `tests/test_ticket_system.py`
- `tests/README.md`
- `tests/e2e/README.md`
