# Backlog

Tracking for bugs, features, improvements, refactors, and todos.

> This file is generated from ticket frontmatter. To update it, edit ticket metadata and run `uv run python scripts/generate_backlog_index.py`.

## Ticket Metadata

Tickets live in `docs/backlog/` as Markdown files with YAML frontmatter.
Filenames are stable and do not need to change when status changes; use the `status` field instead.

| Field | Values / Format | Notes |
| --- | --- | --- |
| `id` | `RN-0001` | Stable ticket identifier. Increment for new tickets. |
| `title` | Text | Human-readable ticket title. |
| `type` | `bug`, `feature`, `improvement`, `refactor`, `todo` | Work category. |
| `status` | `pending`, `in_progress`, `resolved`, `wont_fix` | Drives this index. |
| `priority` | `high`, `medium`, `low` | Used for sorting within status. |
| `created` | `YYYY-MM-DD` | Creation date. |
| `resolved` | `YYYY-MM-DD` or blank | Fill when resolved. |
| `area` | Short slug | Example: `live-roasting`, `testing`, `docs`. |
| `tags` | YAML list | Optional discovery labels. |

Use `docs/backlog/TEMPLATE.md` when creating a new ticket.

## Current Tickets

### Pending

| ID | Type | Priority | Area | Title | Created | Resolved |
| --- | --- | --- | --- | --- | --- | --- |
| RN-0015 | [BUG] | High | database-sync | [Make Database Sync Timestamp-Aware](./RN-0015-timestamp-aware-db-sync.md) | 2026-05-01 | - |
| RN-0016 | [FEATURE] | High | design-system | [New Design System Rollout & Full UI Redesign](./RN-0016-design-system-rollout.md) | 2026-05-01 | - |
| RN-0003 | [TODO] | Medium | testing | [UI/Interface Testing Framework](./RN-0003-ui-interface-testing-framework.md) | 2026-01-11 | - |

### In Progress

No tickets.

## Resolved Tickets

| ID | Type | Priority | Area | Title | Created | Resolved |
| --- | --- | --- | --- | --- | --- | --- |
| RN-0013 | [FEATURE] | Medium | label-creator | [US-4 Sticker Sheet Creator for Bean Labels](./RN-0013-us-4-sticker-sheet-creator.md) | 2026-05-01 | 2026-05-02 |
| RN-0010 | [BUG] | High | live-roasting | [Temperature Sensor Updates Stall During Live Roast](./RN-0010-temperature-update-stalls.md) | 2026-04-24 | 2026-05-02 |
| RN-0014 | [FEATURE] | High | bean-inventory | [Add Short Flavor Note to Beans](./RN-0014-short-flavor-note.md) | 2026-05-01 | 2026-05-01 |
| RN-0012 | [IMPROVEMENT] | Medium | label-creator | [Remember Last-Used Label Template, Font, and Aspect Ratio](./RN-0012-label-template-font-preferences.md) | 2026-04-25 | 2026-04-25 |
| RN-0011 | [FEATURE] | Medium | label-creator | [Rotated (90°) PNG Download and Multi-Line Flavor Notes for Bean Labels](./RN-0011-label-png-rotated-download.md) | 2026-04-25 | 2026-04-25 |
| RN-0009 | [BUG] | High | live-roasting | [Draft Roast Opens As Read-Only Detail Page](./RN-0009-draft-roast-readonly-detail.md) | 2026-04-24 | 2026-04-24 |
| RN-0008 | [TODO] | Medium | docs | [Design Documentation Restructure](./RN-0008-design-documentation-restructure.md) | 2026-04-20 | 2026-04-24 |
| RN-0007 | [IMPROVEMENT] | Medium | label-creator | [Label Creator Redesign](./RN-0007-label-creator-redesign.md) | 2026-04-20 | 2026-04-24 |
| RN-0006 | [BUG] | High | live-roasting | [Live Chart and Data Recording Issues](./RN-0006-live-chart-data-recording-issues.md) | 2026-01-18 | 2026-01-18 |
| RN-0005 | [FEATURE] | Medium | live-roasting | [Live Roast Page - Fullscreen Mode](./RN-0005-live-roast-fullscreen-mode.md) | 2026-01-16 | 2026-01-16 |
| RN-0004 | [IMPROVEMENT] | High | live-roasting | [Live Roast Data Collection Accuracy](./RN-0004-live-roast-data-collection-accuracy.md) | 2026-01-11 | 2026-01-11 |
| RN-0002 | [TODO] | High | testing | [API Testing Framework](./RN-0002-api-testing-framework.md) | 2026-01-11 | 2026-01-11 |
| RN-0001 | [BUG] | High | charting | [Chart Visualization Fixes](./RN-0001-chart-visualization-fixes.md) | 2025-01-09 | 2025-01-10 |
