# RoastLogger Documentation

A personal, mobile-responsive web application for tracking coffee beans, logging detailed roast profiles, and managing inventory.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Architecture](./architecture/) | Data models, API endpoints, tech stack |
| [Design](./design/) | Design principles, tokens, components, screens |
| [Features](./features/) | Detailed feature specifications |
| [Hardware](./hardware/) | Temperature sensor setup (ESP32/K-Type) |
| [Issues](./issues/) | Tickets, epics, human decisions, blockers, and dashboard |
| [Deployment](./deployment/) | Render deployment guide |
| [Audit History](./audit_history/database_mirrors/) | Sanitized database mirror and Settings preflight evidence |

## Project Overview

**RoastLogger** helps home roasters:

- Track green coffee bean inventory with automatic stock management
- Log detailed roast profiles with real-time temperature monitoring
- Record key timing events (Yellowing, First Crack, Second Crack)
- Review and rate roasted coffee batches
- Preview or apply guarded, audited sync between local and online databases

## Tech Stack

- **Backend:** Python Flask
- **Database:** MongoDB (local + Atlas)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Charts:** Chart.js with annotation plugin
- **Temperature Sensor:** ESP32 + MAX31855 K-Type thermocouple
- **Deployment:** Render (gunicorn)

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Stable direct-run and `gunicorn app:app` compatibility entry point |
| `roastlogger/` | Application factory, feature blueprints, configuration, database, and services |
| `models/roast_helpers.py` | Database helper functions |
| `static/js/roast-chart.js` | Shared chart component |
| `static/js/live-roast/` | Live-roast chart, polling/session, and fullscreen modules |
| `templates/roast_live.html` | Live roasting interface |
| `AGENTS.md` | Shared AI-agent workflow and documentation contract |
| `CLAUDE.md` | Claude-specific routing to the shared workflow |

## Documentation Structure

```
docs/
├── README.md              # This file
├── architecture/          # Technical architecture
│   ├── data-models.md     # MongoDB schemas
│   ├── api-endpoints.md   # All API routes
│   └── tech-stack.md      # Technology stack
├── design/                # Design docs (tokens, components, screens)
│   ├── principles.md
│   ├── foundations/       # Color, typography, spacing, dark mode
│   ├── components/        # Buttons, cards, forms, instrument displays
│   ├── screens/           # Per-screen design specs (including sticker sheet modal)
│   └── patterns/          # Recurring design systems (label + sticker templates)
├── features/              # Feature specifications
│   ├── live-roasting.md   # Live roasting interface
│   ├── bean-label-creator.md
│   ├── sticker-sheet.md   # US-4 PDF sticker sheet creator
│   ├── database-sync.md   # Guarded CLI and local Settings sync
│   ├── temperature-sensor.md
│   └── chart-visualization.md
├── hardware/              # Hardware docs
│   └── thermo-sensor.md   # ESP32 K-Type sensor
├── issues/                # RN tickets, HD decisions, and generated workbench
│   ├── README.md          # Generated tracker guide + status navigation
│   ├── overview.html      # Generated self-contained dashboard
│   ├── tracker.toml       # Prefixes, types, and priorities
│   ├── templates/         # Active ticket and human-decision templates
│   ├── pending/           # Ready work
│   ├── in_progress/       # Work underway
│   ├── blocked/           # Work with explicit blockers
│   ├── resolved/          # Completed work
│   ├── wont_fix/          # Intentionally closed work
│   ├── decision-pending/  # Human choices awaiting evidence or a decision
│   └── decision-finalized/# Recorded decisions and outcomes
├── audit_history/         # Sanitized operational audit records and contracts
└── deployment/            # Deployment guides
```

Application code is organized under `roastlogger/`: `create_app()` configures
database connections and template helpers, registers feature-focused
blueprints, and delegates lifecycle, sensor/RoR, live-sync, and
timestamp-aware database-sync behavior to service modules. `app.py` keeps the
historic development, test-import, and Gunicorn entry-point contract.
Applied database sync is available through `scripts/sync_database.py` and the
same guarded phases in Settings when both the direct peer and request host are
loopback. Hosted and non-loopback Settings remain audited, read-only preflight.

## Keeping Docs in Sync

When you change the project, update the docs that describe what you changed — **in the same branch**. Out-of-date docs mislead the next reader (including future-you).

| What you changed | Doc to update |
| --- | --- |
| API route added, changed, or removed | [architecture/api-endpoints.md](./architecture/api-endpoints.md) |
| MongoDB schema / document shape | [architecture/data-models.md](./architecture/data-models.md) |
| New dependency | [architecture/tech-stack.md](./architecture/tech-stack.md) |
| Feature behaviour, lifecycle, or API surface | [features/](./features/) (the matching feature file) |
| **UI / CSS / visual change** — colour, font, spacing, layout, component, screen, design pattern | **[design/](./design/)** — foundations, components, screens, or patterns depending on what changed |
| New screen or major layout change | [design/screens/](./design/screens/) + this README's navigation block |
| Bug fix or any ticketed work | The record under [issues/](./issues/), then regenerate and validate the tracker |

If a single change has both behaviour and visual implications, update the feature doc (behaviour) **and** the design doc (look & feel). Link between them rather than duplicating.

## For AI Assistants

See [AGENTS.md](../AGENTS.md) for the shared workflow. Claude-specific routing
lives in [CLAUDE.md](../CLAUDE.md).
