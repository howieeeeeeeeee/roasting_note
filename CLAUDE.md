# Claude Instructions for RoastLogger

This file provides instructions for AI assistants working on this repository.

## Documentation Requirements

**Important:** When making changes to this repository, update the relevant documentation:

1. **New Features** - Add to `docs/features/` or update existing feature file
2. **Bug Fixes** - Create issue file in `docs/issues/` with resolution details
3. **API Changes** - Update `docs/architecture/api-endpoints.md`
4. **Schema Changes** - Update `docs/architecture/data-models.md`
5. **UI/UX Changes** - Update relevant feature documentation

## File Labels

Use these prefixes in issue/todo files:
- `[FEATURE]` - New functionality
- `[BUG]` - Bug fix
- `[IMPROVEMENT]` - Enhancement to existing feature
- `[REFACTOR]` - Code restructuring without behavior change
- `[DOCS]` - Documentation only

## Documentation Structure

```
docs/
├── README.md              # Overview and navigation
├── architecture/          # Technical architecture
│   ├── README.md          # Architecture overview
│   ├── data-models.md     # MongoDB schemas
│   ├── api-endpoints.md   # All API routes
│   └── tech-stack.md      # Technology stack details
├── features/              # Feature specifications
│   ├── README.md          # Features overview
│   ├── beans-management.md
│   ├── roast-management.md
│   ├── live-roasting.md
│   ├── temperature-sensor.md
│   ├── database-sync.md
│   └── chart-visualization.md
├── hardware/              # Hardware documentation
│   └── thermo-sensor.md   # ESP32 K-Type sensor (separate repo)
├── issues/                # Issue tracking
│   └── README.md          # Issues index
├── todos/                 # Task tracking
│   └── README.md          # Todos index
└── deployment/            # Deployment guides
    └── render.md          # Render deployment
```

## Testing Guidelines

When making major changes:
1. Run the application locally
2. Test affected features manually
3. Verify database operations work correctly
4. Check mobile responsiveness if UI changes

## Code Style

- Use consistent indentation (4 spaces for Python, 2 for HTML/CSS/JS)
- Follow existing naming conventions
- Keep functions focused and small
- Add comments for complex logic only

## Common Tasks

### Adding a New Feature
1. Create/update feature spec in `docs/features/`
2. Implement backend changes in `app.py` or `models/`
3. Implement frontend changes in `templates/` and `static/`
4. Update `docs/architecture/api-endpoints.md` if new routes added
5. Test thoroughly

### Fixing a Bug
1. Document the bug in `docs/issues/` with filename format: `YYYY-MM-{status}-{description}.md`
2. Fix the code
3. Update the issue file with `[RESOLVED]` status and resolution details

### Updating Documentation
- Keep documentation in sync with code
- Use clear, concise language
- Include code examples where helpful
- Update the README.md navigation if adding new sections

## Key Implementation Details

### Temperature Sensor
- Endpoint: `GET /api/temp/current`
- Polls sensor URL from `TEMP_SENSOR_URL` env var
- Makes 3 requests with 100ms timeout each
- Returns average of two highest readings

### Database Switching
- Two DBs: local (home network) and online (Atlas)
- Switch via Settings modal
- Sync operations copy data bidirectionally

### Chart Component
- Shared module: `static/js/roast-chart.js`
- Used by: roast_live.html, roast_detail.html, roast_edit.html
- Power/Fan timeline bars with colored segments
