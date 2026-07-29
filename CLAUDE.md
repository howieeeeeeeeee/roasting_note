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

Generated issue views are read-only. Refresh and validate them with:

```bash
uv run python scripts/generate_issues_index.py
uv run python scripts/generate_issues_index.py --check
```
