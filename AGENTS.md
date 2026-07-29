# RoastLogger Agent Guide

Keep product changes, documentation, tickets, and verification in sync.

## Before Changing The Project

1. Create a branch from `main`: `feat/`, `fix/`, `improve/`, or `docs/`.
2. Read `docs/README.md` for project context.
3. Check `docs/issues/README.md` and related `RN-...` records.
4. Read the feature, design, architecture, hardware, or deployment docs that
   describe the affected behavior.
5. Preserve unrelated user changes already in the worktree.

## Documentation Is Part Of Done

Update durable guidance in the same branch as the change:

| Change | Documentation |
| --- | --- |
| API route | `docs/architecture/api-endpoints.md` |
| Data shape/schema | `docs/architecture/data-models.md` |
| Dependency or runtime | `docs/architecture/tech-stack.md` |
| Feature behavior | Matching `docs/features/` file |
| UI, CSS, layout, or interaction | Matching `docs/design/` foundation, component, screen, or pattern |
| Hardware or deployment | Matching `docs/hardware/` or `docs/deployment/` file |
| Testing workflow | `tests/README.md` |
| Navigation/structure | Relevant `README.md` index |
| Ticketed work | Governing record in `docs/issues/` |

When behavior and appearance both change, update both feature and design docs.
Link between documents instead of duplicating content. The full routing guide is
`.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md`.

## Ticket Tracker

- Use the `ticket-master` skill for `RN-...` tickets, epics, `HD-...` decisions,
  blockers, status changes, and next-work selection.
- Records are filed by status under `docs/issues/`; ids remain stable when paths
  change.
- Use `docs/issues/templates/`, not generated pages, as writing templates.
- Never hand-edit `docs/issues/README.md`, status pages,
  `human-decisions.md`, or `overview.html`.
- After any record change, run:

```bash
uv run python scripts/generate_issues_index.py
uv run python scripts/generate_issues_index.py --check
```

## Verification

Follow `tests/README.md`. Run focused tests while iterating and the full suite
before committing changes to application behavior:

```bash
uv run pytest
```
