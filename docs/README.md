# RoastLogger Documentation

A personal, mobile-responsive web application for tracking coffee beans, logging detailed roast profiles, and managing inventory.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Architecture](./architecture/) | Data models, API endpoints, tech stack |
| [Design](./design/) | Design principles, tokens, components, screens |
| [Features](./features/) | Detailed feature specifications |
| [Hardware](./hardware/) | Temperature sensor setup (ESP32/K-Type) |
| [Backlog](./backlog/) | Bugs, features, improvements, todos |
| [Deployment](./deployment/) | Render deployment guide |

## Project Overview

**RoastLogger** helps home roasters:

- Track green coffee bean inventory with automatic stock management
- Log detailed roast profiles with real-time temperature monitoring
- Record key timing events (Yellowing, First Crack, Second Crack)
- Review and rate roasted coffee batches
- Sync data between local and online databases

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
| `app.py` | Main Flask application with all routes |
| `models/roast_helpers.py` | Database helper functions |
| `static/js/roast-chart.js` | Shared chart component |
| `templates/roast_live.html` | Live roasting interface |
| `CLAUDE.md` | AI assistant instructions |

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
│   ├── screens/           # Per-screen design specs
│   └── patterns/          # Recurring design systems (label templates)
├── features/              # Feature specifications
│   ├── live-roasting.md   # Live roasting interface
│   ├── temperature-sensor.md
│   └── chart-visualization.md
├── hardware/              # Hardware docs
│   └── thermo-sensor.md   # ESP32 K-Type sensor
├── backlog/               # Issue/task tracking
│   ├── README.md          # Backlog overview
│   └── *.md               # Individual items
└── deployment/            # Deployment guides
```

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
| Bug fix or any ticketed work | The ticket under [backlog/](./backlog/), then regenerate the index |

If a single change has both behaviour and visual implications, update the feature doc (behaviour) **and** the design doc (look & feel). Link between them rather than duplicating.

## For AI Assistants

See [CLAUDE.md](../CLAUDE.md) for instructions on working with this repository.
