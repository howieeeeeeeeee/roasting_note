# Architecture Overview

Technical architecture documentation for RoastLogger.

## Contents

| Document | Description |
|----------|-------------|
| [Data Models](./data-models.md) | MongoDB collection schemas |
| [API Endpoints](./api-endpoints.md) | All REST API routes |
| [Tech Stack](./tech-stack.md) | Technologies and dependencies |

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Browser)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   HTML/CSS  │  │  Vanilla JS │  │  Chart.js + Plugin  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────┐
│                    Flask Backend (app.py)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Routes    │  │   Helpers   │  │  Temp Sensor Client │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │ PyMongo
┌────────────────────────────▼────────────────────────────────┐
│                        MongoDB                               │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │   Local Instance    │  │     MongoDB Atlas (Online)   │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Database Architecture

- **Two database connections:** Local (home network) and Online (Atlas)
- **User can switch** between databases via Settings modal
- **Bidirectional sync** available to copy data between databases
- **Collections:** `beans` and `roasts`

## Key Design Decisions

1. **Embedded Documents** - Reviews and temperature curves are embedded in roast documents for atomic operations
2. **Soft Deletion** - Items marked `archived: true` instead of actual deletion
3. **Stock Management** - Bean stock automatically adjusted when roasts are created/archived
4. **Shared Chart Module** - Single `roast-chart.js` used across live, detail, and edit pages
