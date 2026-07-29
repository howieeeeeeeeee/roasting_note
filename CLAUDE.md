# Claude Notes For RoastLogger

Follow [AGENTS.md](./AGENTS.md) as the shared repository policy.

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
