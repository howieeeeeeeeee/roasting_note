---
id:
title:
type: feature
status: pending
priority: medium
created:
resolved:
area:
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags: []
---

# Title

## Description

One or two sentences describing the user-facing outcome and why it matters now.

## Details

- Current behavior:
- Desired change:
- In scope:
- Out of scope:
- Verification:

## Acceptance Criteria

- [ ] Criterion written as a verifiable outcome.
- [ ] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [ ] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

Use `.claude/skills/ticket-master/TESTING_WORKFLOW.md`. Fill every field with
exact paths, scenarios, commands, and evidence. Choose browser level `none`,
`targeted`, or `full`. Use `None` for omitted coverage only with a concrete Not
applicable reason.

- Change classification:
- Browser verification level:
- Automated tests to add or update:
- Browser E2E scenarios to add or update:
- Required commands:
- Required browser evidence:
- Not applicable reason:

## Documentation Impact

- `docs/features/example.md`
- Conditional: `docs/architecture/api-endpoints.md` if an API route changes.

## Database Operations Impact

Complete this section when the ticket changes a MongoDB document shape,
persistence behavior, database route/service, migration/backfill, database
configuration, or synchronization behavior. Otherwise replace the prompts with
`None` only after focused repository reads confirm no live operation is needed.

- Collections and local/online effects:
- Migration or backfill:
- Expected sync direction:
- Is an applied mirror part of delivery:
- Required backup/audit evidence for resolution:

## Open Questions

- None.

## Related Files

- `path/to/file`
