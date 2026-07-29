---
name: ticket-master
description: Create, refine, resolve, or select RoastLogger tickets (`RN-...`) and human decisions (`HD-...`) in docs/issues/. Use for ticket planning, epics, child tickets, status changes, blocker propagation, dashboard maintenance, questions about remaining decisions, statements such as "I decided", or product ideas that should be specified before implementation. Tracker work only; do not implement the underlying product change.
---

# Ticket Master

Read `.claude/skills/ticket-master/SKILL.md` completely and follow it. Read
`.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md` whenever creating,
refining, or resolving a ticket so the affected RoastLogger docs are recorded
and updated with the future implementation. Read
`.claude/skills/ticket-master/TESTING_WORKFLOW.md` for the same ticket
lifecycle so automated coverage and durable UI browser scenarios are declared
and verified. Keep changing test lists in `tests/README.md` and
`tests/e2e/README.md`, not in the skill. For database-impacting tickets, require
the `## Database Operations Impact` contract and resolution evidence; ticketing
work must never perform an applied database mirror.
