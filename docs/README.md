# RoastLogger Documentation

A personal, mobile-responsive web application for tracking coffee beans, logging detailed roast profiles, and managing inventory.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Architecture](./architecture/) | Data models, API endpoints, tech stack |
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

## For AI Assistants

See [CLAUDE.md](../CLAUDE.md) for instructions on working with this repository.
