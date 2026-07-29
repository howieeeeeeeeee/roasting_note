# RoastLogger Agent Guide

Keep product changes, documentation, tickets, and verification in sync.

## Before Changing The Project

1. Create a branch from `main`: `feat/`, `fix/`, `improve/`, or `docs/`.
2. Read `docs/README.md` for project context.
3. Check `docs/issues/README.md` and related `RN-...` records.
4. Read the feature, design, architecture, hardware, or deployment docs that
   describe the affected behavior.
5. Preserve unrelated user changes already in the worktree.

## File Size And Modularity

- Human-authored code and documentation must not exceed 1,000 physical lines
  per file.
- When code would exceed the limit, split it by responsibility into focused
  modules and import, include, or register them from a stable entry point.
- When documentation would exceed the limit, split it into aspect-specific
  documents under a named directory, retain a concise `README.md` index, and
  update all affected navigation links.
- Do not split files into arbitrary numbered chunks. Each resulting file must
  have one clear subject or responsibility and must also remain within the
  limit.
- Generated output, vendored or minified code, binaries, fonts, licenses, and
  lock files are exempt.
- `tests/test_file_size_policy.py` enforces the policy for tracked
  human-authored Python, JavaScript, HTML, CSS, C++, header, and Markdown
  files.

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

## Testing Impact Is Part Of The Ticket

- Every active ticket uses `testing_policy: v1` and records exact automated
  tests, browser scenarios, commands, and evidence under `## Testing Impact`.
- Use `.claude/skills/ticket-master/TESTING_WORKFLOW.md` to classify the change
  and select the required verification.
- Keep the automated test inventory in `tests/README.md` and the durable UI
  regression checklist in `tests/e2e/README.md`; do not duplicate those
  changing lists in tickets or skills.
- Record browser verification as `none`, `targeted`, or `full`. Small low-risk
  visual-only fixes may use `none` with a concrete reason; focused interaction
  changes use `targeted`; critical or cross-workflow behavior uses `full`.
- During ticket creation, ask the user one concise level-selection question
  only when focused reads do not make the appropriate level clear.
- `targeted` and `full` changes add or update their browser scenario. Removed
  UI must remove or revise obsolete scenarios.
- Browser checks supplement focused automated tests and the full pytest suite;
  they do not replace them.

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

## Database-Impacting Work

This workflow applies to MongoDB document shapes, persistence behavior,
database routes or services, migrations, database configuration, and sync:

1. Add a `## Database Operations Impact` section to the ticket. Record affected
   collections, local and online effects, migration or backfill needs, expected
   sync direction, whether an applied mirror is part of delivery, and required
   backup or audit evidence.
2. Read `docs/features/database-sync.md` before implementation. When configured
   endpoints are available, run `scripts/sync_database.py --dry-run`; report an
   unavailable endpoint as an environment limitation unless live evidence is a
   ticket requirement.
3. Use mocks, fixtures, or an isolated local database for implementation and
   automated verification. Never use an applied mirror as a test, startup,
   cleanup, or implicit ticket step.
4. An applied mirror requires a separate explicit user request after its
   preflight is visible and both exact run-specific confirmations. Never infer
   approval, automate either token, reuse earlier consent, or add a bypass.
5. After an applied mirror, the operator reviews the result and manually
   publishes only its audit record. `db_backup/` payloads and manifests remain
   ignored and untracked.
6. Before resolution, record dry-run evidence or the applied run ID and audit
   path, verify the required docs, and confirm
   `git ls-files db_backup 'db_backup/**'` returns no files.

Ticketing turns may specify and verify this workflow but must never perform an
applied database sync.

## Verification

Follow `tests/README.md`. Run focused tests while iterating and the full suite
before committing changes to application behavior:

```bash
uv run pytest
```

For browser level `targeted` or `full`, also update `tests/e2e/README.md`, run
the declared browser scenario, and record its evidence and cleanup in the
ticket. Browser level `none` requires a concrete reason but no browser task.
