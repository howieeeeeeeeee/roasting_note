# Tech Stack

Technologies and dependencies used in RoastLogger.

## Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.x | Programming language |
| Flask | Latest | Web framework |
| PyMongo | Latest | MongoDB driver |
| Gunicorn | Latest | WSGI server (production) |
| python-dotenv | Latest | Environment variables |
| requests | Latest | HTTP client (temp sensor) |

## Frontend

| Technology | Purpose |
|------------|---------|
| HTML5 | Page structure |
| CSS3 | Styling with CSS variables |
| Vanilla JavaScript | Interactivity, API calls |
| Chart.js | Temperature/RoR charts |
| chartjs-plugin-annotation | Event markers on charts |
| Flatpickr | Date/datetime picker (bean purchase date, roast date, label roast date) |
| jsPDF | Client-side PDF generation for US-4 sticker sheets |
| Material Icons | UI icons |
| Inter Font | Typography |
| Roboto Slab | Label creator (Classic template) |

## Database

| Technology | Purpose |
|------------|---------|
| MongoDB | Document database |
| MongoDB Atlas | Cloud-hosted (online mode) |
| Local MongoDB | Self-hosted (local mode) |

## Hardware

| Component | Purpose |
|-----------|---------|
| ESP32 | Microcontroller for sensor |
| MAX31855 | Thermocouple amplifier |
| K-Type Thermocouple | Temperature probe |

## Deployment

| Service | Purpose |
|---------|---------|
| Render | Web hosting (free tier) |
| MongoDB Atlas | Cloud database (M0 free tier) |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Flask entry point | `app.py` |
| `FLASK_ENV` | Environment mode | `production` |
| `SECRET_KEY` | Flask session secret | Required |
| `MONGO_URI` | Online MongoDB connection | Required |
| `MONGO_URI_LOCAL` | Local MongoDB connection | Required |
| `DEFAULT_DB` | Default database mode; invalid values fall back to local | `local` |
| `DEVICE` | Stable per-machine sync/audit identity; blank is rejected by sync | Required for sync |
| `E2E_MODE` | Enable fail-closed dedicated browser-test runtime | `false` |
| `E2E_RUN_ID` | Safe unique marker required when E2E mode is enabled | Empty |
| `E2E_ARTIFACT_ROOT` | Ignored run evidence and log root | Run-scoped path |
| `TEMP_SENSOR_URL` | Temperature sensor endpoint | `http://192.168.0.47/temp` |
| `LOCAL_DB_NAME` | Local MongoDB database name; injectable for isolated runtimes | `roastlogger` |
| `TIMEZONE` | Operator display/storage timezone | `America/New_York` |

---

## File Structure

```
roasting_note/
├── app.py                 # Stable direct-run and Gunicorn entry point
├── roastlogger/
│   ├── factory.py         # create_app(config_overrides=None)
│   ├── config.py          # Environment-backed defaults
│   ├── database.py        # Local/online clients and selected collections
│   ├── blueprints/        # Page, bean, roast, temperature, settings routes
│   └── services/          # Lifecycle, sensor/RoR, live-sync, database sync
├── scripts/
│   └── sync_database.py   # Guarded dry-run/applied database mirror CLI
├── db_backup/             # Ignored Extended JSON destination backups
├── docs/audit_history/    # Reviewable append-only database mirror audits
├── models/
│   └── roast_helpers.py   # Database helper functions
├── static/
│   ├── css/
│   │   └── style.css      # All styles
│   └── js/
│       ├── roast-chart.js # Shared chart component
│       ├── live-roast/    # Live chart, session/polling, fullscreen entry
│       ├── label-creator.js # Bean label canvas renderer
│       ├── sticker-sheet.js # US-4 sticker sheet modal/export
│       └── jspdf.umd.min.js # Vendored jsPDF browser build
├── templates/
│   ├── base.html          # Base template
│   ├── index.html         # Dashboard
│   ├── beans_*.html       # Bean pages
│   └── roast_*.html       # Roast pages
├── temp_logs/             # Local CSV temperature logs
├── tests/e2e/             # Dedicated runtime, virtual sensor, cleanup, runbook
│   ├── manage.py          # Start and run-scoped cleanup commands
│   ├── virtual_sensor.py  # Deterministic ESP32-compatible scenarios
│   └── artifacts/         # Ignored browser/log/evidence output
├── docs/                  # Documentation
├── .agents/skills/        # Repository-local Codex skill discovery
├── .claude/skills/        # Repository-local skill instructions and resources
│   └── ticket-master/scripts/tracker/ # Tracker models, validation, filing, rendering
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (local)
├── .env.example           # Example environment file
├── AGENTS.md              # Shared AI-agent workflow
└── CLAUDE.md              # Claude-specific routing
```

`app.py` exports the default `app` created by the factory and continues to
support both `python app.py` and `gunicorn app:app`. Tests and specialized
local runtimes can call `create_app()` with configuration overrides without
changing production defaults.

In E2E mode, `roastlogger.database.DatabaseConnections` constructs only the
loopback local client for database `roastlogger_e2e`; `online_client` and
`online_db` are `None`. The factory rejects remote local/sensor hosts, unsafe
run IDs, or any other database name before client initialization.

---

## requirements.txt

```
Flask>=2.0
pymongo>=4.0
gunicorn>=20.0
python-dotenv>=0.19
requests>=2.26
pytz>=2021.1
```
