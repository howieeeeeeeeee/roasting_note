# Issues

Issue and human-decision tracker for RoastLogger. Product, engineering, design, documentation, and hardware work for the RoastLogger application.

> Generated from frontmatter by `.claude/skills/ticket-master/scripts/generate_issues_index.py`. Do not edit by hand.
> Run `uv run python scripts/generate_issues_index.py` from the repository root after editing any record.

## Status Overviews

- [Visual Overview](./overview.html) — self-contained offline dashboard
- [In Progress](./in-progress.md) — 0
- [Blocked](./blocked.md) — 0
- [Pending](./pending.md) — 0
- [Done](./done.md) — 22 (resolved 21, won't-fix 1)
- [Human Decisions](./human-decisions.md) — 0 pending, 0 finalized

## Folder Layout

- File every epic and ticket by its own status under `pending/`, `in_progress/`, `blocked/`, `resolved/`, or `wont_fix/`.
- File a child ticket in an epic-named folder within its own status directory.
- File human decisions under `decision-pending/` or `decision-finalized/`.
- Keep ticket and decision templates under `templates/`.
- Treat ids as stable; status transitions change paths.

## Ticket Metadata

| Field | Values / Format | Notes |
| --- | --- | --- |
| `id` | `RN-0001` or `RN-0001-01` | Stable epic/ticket id. |
| `title` | Text | Human-readable title. |
| `type` | `epic`, `bug`, `feature`, `improvement`, `refactor`, `todo` | Epics group child tickets; other values categorize work. |
| `status` | `in_progress`, `blocked`, `pending`, `resolved`, `wont_fix` | Drives filing and overviews. |
| `priority` | `high`, `medium`, `low` | Sort order within a status. |
| `created` / `resolved` | `YYYY-MM-DD` | Completed work requires a resolution date. |
| `parent` | `RN-XXXX` or blank | Parent epic for child tickets. |
| `decisions` | List of `HD-XXXX` ids | Durable decision provenance. |
| `blocked_by` | List of unresolved `HD-XXXX` or `RN-...` ids | Current blockers; nonempty exactly when status is blocked. |
| `area` / `tags` | Slug / YAML list | Discovery metadata. |

Use `docs/issues/templates/TICKET.md` for work and `docs/issues/templates/HUMAN_DECISION.md` for human choices.

## Human-Decision Metadata

| Field | Values / Format | Notes |
| --- | --- | --- |
| `id` | `HD-XXXX` | Sequential human-decision id. |
| `type` | `human-decision` | Separates decisions from implementation work. |
| `status` | `pending`, `finalized` | Finalized requires an outcome and date. |
| `outcome` | Allowed outcome key or blank | Exact recorded choice after finalization. |
| `decided_by` | Name/role or blank | Optional provenance. |
| `blocked_by` | Unfinished ticket or pending-decision ids | Empty means ready for review; nonempty means waiting for evidence. |

## Block Logic

A ticket is `blocked` exactly when `blocked_by` is nonempty. A pending decision is ready exactly when `blocked_by` is empty. Finalizing a decision or resolving a ticket removes only that id from downstream blockers. A blocked ticket becomes pending only after no blockers remain.

## Documentation Gate

Every new or refined ticket records exact documentation targets under `## Documentation Impact`. Before resolution, compare the implementation diff with `.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md` and update every affected document in the same branch.
