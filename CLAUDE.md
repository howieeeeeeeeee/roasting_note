# Claude Instructions for RoastLogger

## Documentation Structure

```text
docs/
├── README.md              # Start here - navigation & overview
├── architecture/          # Data models, API routes, tech stack
├── features/              # Feature specifications
├── hardware/              # ESP32 temperature sensor docs
├── backlog/               # Bugs, features, todos (combined)
└── deployment/            # Render deployment guide
```

## Workflow

### Branch Strategy

Create feature branches for new work:

```bash
# Feature branches
git checkout -b feat/<feature-name>

# Bug fixes
git checkout -b fix/<bug-name>

# Improvements
git checkout -b improve/<improvement-name>
```

### Before Making Changes

1. Create a new branch from `main` for the work
2. Read `docs/README.md` for project overview
3. Check `docs/backlog/README.md` for related issues/todos
4. Read relevant feature docs in `docs/features/`

### After Making Changes

Update these docs as needed:

| Change Type | Update |
| --- | --- |
| New API route | `docs/architecture/api-endpoints.md` |
| Schema change | `docs/architecture/data-models.md` |
| New feature | Create/update file in `docs/features/` |
| Bug fix | Add/update ticket metadata in `docs/backlog/`, then regenerate the backlog index |
| New dependency | `docs/architecture/tech-stack.md` |

### Must Stay in Sync

These files MUST be updated when structure changes:

- `docs/README.md` - Main navigation
- `docs/backlog/README.md` - Generated backlog index; do not edit manually

## Backlog Workflow

Backlog tickets live in `docs/backlog/` as Markdown files with YAML frontmatter.
Filenames are stable and do not need to change when a ticket changes status.

Use `docs/backlog/TEMPLATE.md` for new tickets. Assign the next `RN-XXXX` ID by checking `docs/backlog/README.md` or existing ticket frontmatter.

Required frontmatter fields:

```yaml
id: RN-XXXX
title: Short Ticket Title
type: bug
status: pending
priority: medium
created: YYYY-MM-DD
resolved:
area: live-roasting
tags:
  - example-tag
```

Allowed values:

- `type`: `bug`, `feature`, `improvement`, `refactor`, `todo`
- `status`: `pending`, `in_progress`, `resolved`, `wont_fix`
- `priority`: `high`, `medium`, `low`

After adding or changing any backlog ticket metadata, regenerate the index:

```bash
uv run python scripts/generate_backlog_index.py
```

Do not hand-edit the generated ticket tables in `docs/backlog/README.md`.

## Quick Reference

| Need to... | Go to |
| --- | --- |
| Understand the project | `docs/README.md` |
| See API routes | `docs/architecture/api-endpoints.md` |
| See DB schema | `docs/architecture/data-models.md` |
| Check pending work | `docs/backlog/README.md` |
| Understand a feature | `docs/features/` |
| Run tests | `tests/README.md` |

## Testing Requirements

### When to Run Tests

**ALWAYS run tests in these situations:**

1. **After major feature changes** - Any change that affects API endpoints, database operations, or business logic
2. **After adding new features** - Write tests for new functionality before or alongside implementation
3. **When user requests testing** - Run full test suite or specific tests as requested
4. **Before committing** - Verify tests pass before finalizing changes

### Running Tests

```bash
# Install test dependencies (first time only)
uv add --dev pytest pytest-flask

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_beans_api.py
uv run pytest tests/test_roasts_api.py

# Run with verbose output
uv run pytest -v
```

### Writing Tests for New Features

When implementing a new API feature:

1. Add tests to appropriate file in `tests/` directory
2. Mark test data with `test_data: True` field
3. Use fixtures from `tests/conftest.py` for setup/teardown
4. Cover both success and error cases

Example test structure:

```python
def test_new_feature(client, beans_collection):
    # Arrange - set up test data
    # Act - call the API
    # Assert - verify results
    # Cleanup handled by fixtures
```

### Test Data Management

- All test data is marked with `test_data: True`
- Tests run against local database only
- Cleanup script: `python tests/cleanup_test_data.py`

### Test Coverage Areas

| Area | Test File |
| --- | --- |
| Bean CRUD, stock | `test_beans_api.py` |
| Roast lifecycle | `test_roasts_api.py` |
| Reviews | `test_reviews_api.py` |
| Temperature/RoR | `test_temperature_api.py` |
