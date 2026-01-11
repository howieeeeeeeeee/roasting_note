# Backlog

Tracking for bugs, features, improvements, and todos.

## Labels

| Label | Description | Example |
|-------|-------------|---------|
| `[FEATURE]` | New functionality to add | Temperature sensor integration |
| `[BUG]` | Something broken that needs fixing | Dropdown menu not responding |
| `[IMPROVEMENT]` | Enhancement to existing feature | Better chart colors |
| `[REFACTOR]` | Code restructuring | Extract shared chart module |
| `[TODO]` | General task or chore | Update documentation |

## Status

| Status | Description |
|--------|-------------|
| `PENDING` | Not started |
| `IN_PROGRESS` | Currently being worked on |
| `RESOLVED` | Completed |
| `WONT_FIX` | Decided not to implement |

## File Naming Convention

```
YYYY-MM-{status}-{short-description}.md
```

Examples:
- `2025-01-resolved-chart-visualization.md`
- `2025-01-pending-test-framework.md`

---

## Current Items

### Pending

| ID | Type | Description | File |
|----|------|-------------|------|
| 1 | [TODO] | Original test framework (legacy) | [2026-01-pending-test-framework.md](./2026-01-pending-test-framework.md) |
| 2 | [TODO] | UI testing | [2026-01-pending-ui-testing.md](./2026-01-pending-ui-testing.md) |

### Resolved (Recent)

| ID | Type | Description | File |
|----|------|-------------|------|
| 1 | [IMPROVEMENT] | Data collection (RoR + DB logging) | [2026-01-resolved-data-collection-improvements.md](./2026-01-resolved-data-collection-improvements.md) |
| 2 | [TODO] | API testing framework (58 tests) | [2026-01-resolved-api-testing.md](./2026-01-resolved-api-testing.md) |
| 3 | [BUG] | Chart visualization fixes | [2025-01-resolved-chart-fixes.md](./2025-01-resolved-chart-fixes.md) |
| 4 | [FEATURE] | Real-time graph with temp/RoR | [2025-01-resolved-realtime-graph.md](./2025-01-resolved-realtime-graph.md) |
| 5 | [FEATURE] | Database sync/switch | [2025-01-resolved-db-sync.md](./2025-01-resolved-db-sync.md) |
| 6 | [FEATURE] | Ambient temp/humidity fields | [2025-01-resolved-ambient-data.md](./2025-01-resolved-ambient-data.md) |

---

## Adding New Items

1. Create a new file in this folder with the naming convention
2. Use the template below
3. Update the "Current Items" table in this README

### Template

```markdown
# [TYPE] Short Description

**Status:** PENDING | IN_PROGRESS | RESOLVED
**Created:** YYYY-MM-DD
**Resolved:** YYYY-MM-DD (if applicable)

## Description

Brief description of the issue/feature/task.

## Details

- Detailed requirements
- Acceptance criteria
- Technical notes

## Resolution (if resolved)

What was done to resolve this item.

## Related Files

- `path/to/file.py`
- `path/to/template.html`
```
