---
id: RN-0023
title: Enforce Ticket Testing Impact
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
---

# Enforce Ticket Testing Impact

## Description

Make automated and browser verification a durable part of ticket creation,
refinement, and resolution so new UI behavior cannot silently omit regression
coverage.

## Details

- Current behavior: Tickets have a generic Verification field but no required
  testing-impact contract or automatic validation for UI browser scenarios.
- Desired change: Route ticket work through a testing workflow, keep canonical
  inventories in test documentation, and reject incomplete active tickets.
- In scope: Skill guidance, ticket templates, tracker validation, generated
  tracker guidance, repository instructions, test documentation, and focused
  policy tests.
- Out of scope: Product UI changes, browser automation dependencies, and CI
  browser execution.
- Verification: Focused tracker tests, deterministic tracker generation, the
  generated-output stale check, file-size policy, and the full pytest suite.

## Acceptance Criteria

- [x] Active tickets require `testing_policy: v1` and complete Testing Impact
  fields.
- [x] UI testing classifications require named browser scenarios and evidence.
- [x] Completed policy tickets require a checked Testing Impact acceptance
  criterion.
- [x] Ticket-master routes creation, refinement, and resolution through the
  testing workflow without duplicating the changing test catalogs.
- [x] The ticket template records exact automated tests, browser scenarios,
  commands, evidence, and any concrete Not applicable reason.
- [x] The automated test inventory and durable UI checklist have explicit
  canonical ownership and drift checks.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: backend-api, refactor
- Automated tests to add or update: `tests/test_ticket_system.py`
- Browser E2E scenarios to add or update: None
- Required commands: `uv run pytest tests/test_ticket_system.py`; `uv run python scripts/generate_issues_index.py`; `uv run python scripts/generate_issues_index.py --check`; `uv run pytest`
- Required browser evidence: None
- Not applicable reason: Ticket workflow and validation behavior have no product UI interaction.

## Documentation Impact

- `.agents/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/SKILL.md`
- `.claude/skills/ticket-master/TESTING_WORKFLOW.md`
- `.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md`
- `.claude/skills/ticket-master/templates/TICKET.md`
- `docs/issues/templates/TICKET.md`
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

- Added a concise testing workflow with risk classifications and canonical
  ownership for automated and browser test lists.
- Added Testing Impact to both active and bundled ticket templates and routed
  ticket-master through it for creation, refinement, resolution, and handoff.
- Added tracker validation for policy presence, required fields, UI browser
  coverage, concrete omission reasons, and checked completion evidence.
- Added canonical inventory and UI checklist maintenance rules with regression
  tests that detect missing test modules or policy text.
- Verification passed: 12 focused tracker tests, deterministic generator,
  generated-output check, and 151 full-suite tests.

## Related Files

- `.claude/skills/ticket-master/TESTING_WORKFLOW.md`
- `.claude/skills/ticket-master/scripts/tracker/validation.py`
- `.claude/skills/ticket-master/scripts/tracker/rendering.py`
- `docs/issues/templates/TICKET.md`
- `tests/test_ticket_system.py`
- `tests/README.md`
- `tests/e2e/README.md`
