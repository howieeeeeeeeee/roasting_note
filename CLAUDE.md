# Claude Notes For RoastLogger

Follow [AGENTS.md](./AGENTS.md) as the shared repository policy.

Keep every human-authored code and documentation file at or below 1,000
physical lines. Split oversized code by responsibility into imported,
included, or registered modules. Split oversized documentation by aspect under
a named directory with a concise `README.md` index and updated navigation.
Apply the exemptions for generated, vendored, minified, binary, font, license,
and lock files defined in `AGENTS.md`. The tracked-file guard lives in
`tests/test_file_size_policy.py`.

For ticket planning, epics, human decisions, blockers, status transitions, or
next-work questions, read and follow
`.claude/skills/ticket-master/SKILL.md`. Ticketing updates tracker records but
does not implement application work.

For any scoped product change, use
`.claude/skills/ticket-master/DOCUMENTATION_WORKFLOW.md` to identify the
feature, design, architecture, hardware, deployment, testing, and navigation
docs that must change in the same branch.

Use `.claude/skills/ticket-master/TESTING_WORKFLOW.md` to record focused
automated tests and durable browser scenarios under the ticket's
`## Testing Impact`. New or changed visible UI must update
`tests/e2e/README.md`; keep the changing test catalogs in `tests/`, not in
skills or tickets.

For database-impacting work, follow the guarded workflow in `AGENTS.md`:
document database operations in the ticket, read
`docs/features/database-sync.md`, use read-only dry runs and isolated automated
tests, and treat an applied mirror as a separate user-authorized operation that
requires both exact run-specific confirmation tokens. Never perform an applied
mirror during a ticketing turn. Publish only its reviewed audit record; never
stage `db_backup/`.

Generated issue views are read-only. Refresh and validate them with:

```bash
uv run python scripts/generate_issues_index.py
uv run python scripts/generate_issues_index.py --check
```
