# Claude Instructions for RoastLogger

## Documentation Structure

```
docs/
├── README.md              # Start here - navigation & overview
├── architecture/          # Data models, API routes, tech stack
├── features/              # Feature specifications
├── hardware/              # ESP32 temperature sensor docs
├── backlog/               # Bugs, features, todos (combined)
└── deployment/            # Render deployment guide
```

## Workflow

### Before Making Changes

1. Read `docs/README.md` for project overview
2. Check `docs/backlog/README.md` for related issues/todos
3. Read relevant feature docs in `docs/features/`

### After Making Changes

Update these docs as needed:

| Change Type | Update |
|-------------|--------|
| New API route | `docs/architecture/api-endpoints.md` |
| Schema change | `docs/architecture/data-models.md` |
| New feature | Create/update file in `docs/features/` |
| Bug fix | Add resolved item to `docs/backlog/` |
| New dependency | `docs/architecture/tech-stack.md` |

### Must Stay in Sync

These files MUST be updated when structure changes:

- `docs/README.md` - Main navigation
- `docs/backlog/README.md` - Current items table

## Backlog Labels

Use in filenames and content:

- `[FEATURE]` - New functionality
- `[BUG]` - Bug fix
- `[IMPROVEMENT]` - Enhancement
- `[TODO]` - Task/chore

File naming: `YYYY-MM-{status}-{description}.md`

## Quick Reference

| Need to... | Go to |
|------------|-------|
| Understand the project | `docs/README.md` |
| See API routes | `docs/architecture/api-endpoints.md` |
| See DB schema | `docs/architecture/data-models.md` |
| Check pending work | `docs/backlog/README.md` |
| Understand a feature | `docs/features/` |
