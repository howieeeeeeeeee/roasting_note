---
name: ticket-master
description: "Create, refine, resolve, or select RoastLogger tickets (`RN-...`) and record or finalize human decisions (`HD-...`) in `docs/issues/`. Use for ticket planning, epics and child tickets, status changes, blocker propagation, dashboard maintenance, questions about remaining decisions, statements such as 'I decided', or product ideas that should be specified before implementation. Requirements and tracker maintenance only: update tracker records, but do not implement the underlying product work."
---

# Ticket Master

Turn RoastLogger work and unresolved human choices into concise, actionable
records. Tickets track work. Human-decision records capture choices that require
a person and make downstream blockers explicit.

## Guardrails

- Do not implement application work while using this skill.
- During an ordinary ticketing turn, edit only `docs/issues/**`.
- During explicit ticket-system maintenance, also edit this skill, its bundled
  resources, tests, and repository guidance requested by the user.
- Before changing the generated dashboard, read `html/INSTRUCTIONS.md`
  completely.
- Read the applicable active template before writing:
  - `docs/issues/templates/TICKET.md`
  - `docs/issues/templates/HUMAN_DECISION.md`
- Preserve ids and history. Status transitions change paths, not ids.
- Ask only about choices that materially change scope, dependencies,
  acceptance, or verification. Keep other unknowns as Open Questions.
- Regenerate and validate the tracker after every record change.
- Do not hand-edit generated Markdown views or `docs/issues/overview.html`.
- Ticketing turns define and verify database-operation requirements but never
  perform an applied database mirror.

## Core Flow

1. Choose the mode: create/refine a ticket or epic, create/finalize a human
   decision, resolve a record, or recommend the next work.
2. Read `docs/issues/README.md`, the applicable template, related records, and
   the minimum product/docs context needed for accurate requirements.
3. Read `DOCUMENTATION_WORKFLOW.md` completely and identify every document the
   future implementation must update.
4. Read `TESTING_WORKFLOW.md` completely and identify focused automated tests,
   durable browser scenarios, commands, and evidence the implementation needs.
5. For database-impacting work, add and evaluate the required
   `## Database Operations Impact` section.
6. Ask only missing questions that change record shape.
7. Update records and propagate blockers across tickets and decisions.
8. Run the generator, fix every validation error, and review the generated
   Markdown views and dashboard.
9. Hand off changed ids, current paths, blockers, documentation impact, testing
   impact, and the next action.

## Record Model

Read project labels and allowed values from `docs/issues/tracker.toml`.

Tickets use:

- `RN-XXXX` for epics and standalone work;
- `RN-XXXX-XX` for child tickets, with `parent: RN-XXXX`;
- types `epic`, `bug`, `feature`, `improvement`, `refactor`, or `todo`;
- priorities `high`, `medium`, or `low`; and
- statuses `pending`, `in_progress`, `blocked`, `resolved`, or `wont_fix`.

Every ticket includes these relationship fields, even when empty:

```yaml
parent:
decisions: []
blocked_by: []
```

- `decisions` is durable provenance. Retain every governing `HD-XXXX` id after
  finalization.
- `blocked_by` is current state. List unresolved decisions and unfinished
  tickets that prevent work from starting.

Human decisions use sequential ids such as `HD-0001`,
`type: human-decision`, and status `pending` or `finalized`.

- A pending decision with no blockers is ready for human review.
- A pending decision with blockers is waiting for evidence.
- A finalized decision records `finalized`, `outcome`, rationale, and the
  decider when known.

## Block And Dependency Logic

Treat frontmatter as authoritative:

- A ticket is `blocked` exactly when `blocked_by` is nonempty.
- Every blocker is an existing pending decision or unfinished ticket.
- Every pending decision must block at least one ticket.
- A decision blocker on a ticket must also remain in its `decisions` list.
- Consequential human choices use `HD-...` records, not unnamed prose blockers.
- Finalizing a decision or resolving a ticket removes only that id from
  downstream `blocked_by` lists.
- A blocked ticket becomes `pending` only after its final blocker is removed.
- Never move `in_progress`, `resolved`, or `wont_fix` work backward
  automatically.
- If an outcome makes work unnecessary, use `wont_fix`, fill `resolved`, and
  explain why in `## Resolution`.
- Keep Details, Open Questions, and Acceptance Criteria consistent with
  frontmatter dependencies.

## Files And Layout

```text
docs/issues/
  tracker.toml
  overview.html
  README.md
  pending.md
  in-progress.md
  blocked.md
  done.md
  human-decisions.md
  templates/
    TICKET.md
    HUMAN_DECISION.md
  pending/
  in_progress/
  blocked/
  resolved/
  wont_fix/
  decision-pending/
  decision-finalized/
```

File every epic and ticket under its own status. File child tickets inside an
epic-named folder within that status. File decisions separately by decision
status. Use stable ids, rather than hard-coded paths, when relating records.

## New Ticket Or Epic

1. Read the generated tracker overview, relevant status page, and ticket
   template.
2. Ground the request with focused reads of related tickets, product docs, code,
   and tests.
3. Establish:
   - user/trigger and current versus desired behavior;
   - scope and explicit exclusions;
   - parent epic or standalone placement;
   - verification and acceptance;
   - dependencies and human decisions;
   - priority, type, area, and external effects; and
   - documentation impact using `DOCUMENTATION_WORKFLOW.md`; and
   - testing impact using `TESTING_WORKFLOW.md`.
4. When database behavior may change, include `## Database Operations Impact`
   with collections, local and online effects, migration/backfill needs, sync
   direction, whether an applied mirror is delivery scope, and required
   backup/audit evidence. Use `None` only after focused repository reads show
   no live database operation is needed.
5. Pick the next top-level id, or the next child suffix under an epic. Use a
   short lowercase kebab filename.
6. Write explicit `parent`, `decisions`, and `blocked_by` fields.
7. Include `testing_policy: v1`, `## Testing Impact`, and the testing acceptance
   checkbox. New or changed visible UI must name the exact scenario to add or
   update in `tests/e2e/README.md`.
8. Include `## Documentation Impact` and a documentation acceptance checkbox.
9. Update the parent epic roadmap when applicable.
10. Run the generator and fix every error.

Create an epic only for a meaningful multi-ticket outcome. Do not create empty
epics or speculative child stubs.

## Human Decisions

### Create

1. Pick the next `HD-XXXX` id.
2. State one exact question, allowed outcomes, evidence, and deterministic
   outcome actions.
3. Add unfinished evidence records to the decision's `blocked_by`, or use an
   empty list when it is ready now.
4. Add the decision id to `decisions` on every related ticket.
5. Add it to ticket `blocked_by` only where work truly cannot begin.
6. Leave `finalized` and `outcome` blank.
7. Run the generator and review readiness and related work.

### Finalize When The User Says "I Decided"

1. Read the decision and every ticket that lists it in `decisions`.
2. Match the user's statement to an allowed outcome; ask only when ambiguous.
3. Set status to `finalized`; record the date, exact outcome, rationale, and
   decider when known.
4. Apply the declared outcome actions.
5. Retain the decision id in all durable `decisions` lists.
6. Remove it from downstream `blocked_by` lists.
7. Recompute downstream statuses and decision readiness.
8. Run the generator and report what was released, stayed blocked, resolved, or
   became `wont_fix`.

## Resolve A Ticket

1. Verify every acceptance criterion.
2. Read the implementation diff and `TESTING_WORKFLOW.md`; confirm every
   declared automated test and browser scenario was added, updated, and run.
3. Confirm durable new or changed UI interactions are synchronized with
   `tests/e2e/README.md` and record browser evidence and cleanup.
4. Read the implementation diff and `DOCUMENTATION_WORKFLOW.md`; confirm all
   affected docs were updated in the same branch.
5. Update `## Testing Impact` and `## Documentation Impact` if implementation
   changed either expected set.
6. For database-impacting work, verify the resolution records either dry-run
   evidence or the applied run ID and audit path, plus confirmation that no
   `db_backup/` file is tracked. An applied mirror is never performed by this
   skill.
7. Add concise `## Resolution` notes, including verification, browser evidence
   when applicable, and docs updated.
8. Set status to `resolved` or `wont_fix` and fill `resolved`.
9. Remove this id from downstream blockers and recompute their statuses.
10. Run the generator and review every moved record and generated view.

Do not mark a ticket complete while required testing, browser evidence, or
documentation is missing.

## Choose The Next Work

1. Read `pending.md`, `in-progress.md`, `blocked.md`, and
   `human-decisions.md`.
2. Separate actionable pending tickets from blocked work.
3. Separate ready decisions from decisions waiting on evidence and state what
   each decision would unlock.
4. Recommend one next action and identify it as human review or implementation.
5. Do not start implementation in the same ticketing turn.

## Generation And Validation

Run from the repository root:

```bash
uv run python scripts/generate_issues_index.py
uv run python scripts/generate_issues_index.py --check
```

The compatibility command delegates to this skill's generator. It validates
ids, types, statuses, parents, decisions, blockers, cycles, and canonical paths;
files records by status; refreshes Markdown indexes and decision related-work
tables; and regenerates the offline dashboard.

## RoastLogger Documentation Gate

Read `DOCUMENTATION_WORKFLOW.md` completely for the repository structure and
routing table. In summary:

- update architecture docs for routes, schemas, dependencies, or structural
  changes;
- update feature docs for behavior;
- update design docs for visual or interaction changes;
- update hardware or deployment docs when those surfaces change;
- update `docs/README.md` or local indexes when navigation changes; and
- update the governing ticket for ticketed implementation.

When a change spans behavior and appearance, require both feature and design
documentation and link between them instead of duplicating prose.

## RoastLogger Testing Gate

Read `TESTING_WORKFLOW.md` completely for classification and resolution rules.
Keep the automated catalog in `tests/README.md` and the durable UI regression
checklist in `tests/e2e/README.md`; do not duplicate either changing list in
this skill. Every new or refined active ticket uses `testing_policy: v1` and
records exact automated tests, browser scenarios, commands, and evidence under
`## Testing Impact`.

New or changed visible UI must update the browser checklist. Browser coverage
supplements focused automated coverage and the full pytest suite. Resolution
records the declared commands and, when applicable, browser run ID, evidence,
console/network findings, and scoped cleanup.

For database-impacting tickets, require the database operations section and
route it through the guarded workflow in `DOCUMENTATION_WORKFLOW.md`. Applied
mirrors require separate user authorization after preflight and both
run-specific confirmations; ticket maintenance never supplies those
confirmations.

## Handoff

Report:

- created or updated ids and current paths;
- remaining decisions and Open Questions;
- actionable versus blocked work with blocker ids;
- testing and documentation targets; and
- the next separate implementation or human-review action.
