## Why

RoastLogger has a fully working application with no OpenSpec documentation. This change retroactively
captures the existing system's behavior as a formal spec baseline — so future changes have a foundation
to build on, delta specs have something to diff against, and requirements are explicit and testable.

## What Changes

- **New**: 9 capability specs covering every major functional area of the application
- No code changes — this is a documentation-only change

## Capabilities

### New Capabilities

- `bean-management`: CRUD, stock tracking, filtering, and archival of green coffee bean inventory
- `roast-lifecycle`: Full roast session lifecycle — creation, editing, archival, and state transitions
- `temperature-tracking`: Real-time K-Type sensor reading with 3-request averaging and RoR calculation
- `live-roasting`: Live control interface — timer, sensor polling, fan/power controls, periodic DB logging
- `chart-visualization`: Chart.js temperature and RoR chart with event annotations and power/fan bands
- `roast-timing`: Key timing event logging (Yellowing, First Crack, etc.) and continuous temp curve recording
- `roast-reviews`: Post-roast tasting notes and scores embedded in roast documents
- `database-sync`: Bidirectional sync between local MongoDB and MongoDB Atlas
- `settings-configuration`: Runtime configuration of sensor URL, database mode, and dev utilities

### Modified Capabilities

<!-- None — this is the initial baseline. No existing specs to modify. -->

## Impact

- `openspec/specs/` — 9 new capability folders created, each with a `spec.md`
- No application code, tests, or docs are affected
