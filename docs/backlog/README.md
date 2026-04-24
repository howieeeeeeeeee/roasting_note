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
YYYY-MM-DD-{status}-{short-description}.md
```

Examples:
- `2025-01-18-resolved-chart-visualization.md`
- `2025-01-18-pending-test-framework.md`

Note: older tickets may still use `YYYY-MM-...` until they are renamed.

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
| 0 | [IMPROVEMENT] | Label creator redesign (4 templates, font presets, aspect ratio) | [2026-04-20-backlog-label-creator-update.md](./2026-04-20-backlog-label-creator-update.md) |
| 1 | [BUG] | Live chart and data recording issues (RoR filter, Drop event, layout) | [2026-01-resolved-live-chart-improvements.md](./2026-01-resolved-live-chart-improvements.md) |
| 2 | [FEATURE] | Fullscreen mode for live roast page | [2026-01-resolved-fullscreen-mode.md](./2026-01-resolved-fullscreen-mode.md) |
| 3 | [IMPROVEMENT] | Data collection (RoR + DB logging) | [2026-01-resolved-data-collection-improvements.md](./2026-01-resolved-data-collection-improvements.md) |
| 4 | [TODO] | API testing framework (58 tests) | [2026-01-resolved-api-testing.md](./2026-01-resolved-api-testing.md) |
| 5 | [BUG] | Chart visualization fixes | [2025-01-resolved-chart-fixes.md](./2025-01-resolved-chart-fixes.md) |
| 6 | [FEATURE] | Real-time graph with temp/RoR | [2025-01-resolved-realtime-graph.md](./2025-01-resolved-realtime-graph.md) |
| 7 | [FEATURE] | Database sync/switch | [2025-01-resolved-db-sync.md](./2025-01-resolved-db-sync.md) |
| 8 | [FEATURE] | Ambient temp/humidity fields | [2025-01-resolved-ambient-data.md](./2025-01-resolved-ambient-data.md) |

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
