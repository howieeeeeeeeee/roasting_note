# API Test Suite

API-level tests for RoastLogger backend operations.

## When to Run Tests

Run the test suite in these situations:

1. **After changes to API endpoints, database operations, or business logic** — any change that could regress backend behaviour.
2. **After adding new features** — write tests alongside the implementation, not after.
3. **Before committing** — verify the suite passes before finalising changes.
4. **When explicitly requested** — running specific tests or the full suite on demand.
5. **After ticket-system changes** — run the tracker tests and stale-generation check after changing its schema, templates, generator, dashboard, or skill.

For pure UI / CSS / documentation changes, running the API test suite is usually unnecessary — but it is always safe.

## Setup

Install test dependencies using uv (recommended):

```bash
uv add --dev pytest pytest-flask
```

Or install with pip:

```bash
pip install pytest pytest-flask
```

## Running Tests

Run all tests:

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Run specific test file:

```bash
uv run pytest tests/test_beans_api.py
uv run pytest tests/test_roasts_api.py
uv run pytest tests/test_reviews_api.py
uv run pytest tests/test_temperature_api.py
uv run pytest tests/test_ticket_system.py
uv run pytest tests/test_database_sync.py
uv run pytest tests/test_database_backup.py
uv run pytest tests/test_database_sync_cli.py
uv run pytest tests/test_database_sync_routes.py
uv run pytest tests/test_e2e_runtime.py
uv run pytest tests/test_virtual_sensor.py
uv run pytest tests/test_api_contracts.py
```

Run specific test class or method:

```bash
uv run pytest tests/test_beans_api.py::TestBeanCreate
uv run pytest tests/test_beans_api.py::TestBeanCreate::test_create_bean_valid_data
```

Run tests matching a pattern:

```bash
uv run pytest -k "stock"  # All tests with "stock" in name
uv run pytest -k "create or delete"  # Tests with "create" or "delete"
```

## Test Coverage

### Bean Operations (`test_beans_api.py`)
- Create bean with valid/invalid data
- Edit bean details
- Delete bean (soft delete verification)
- Stock management
- Unit price calculation
- Form validation and data handling

### Roast Operations (`test_roasts_api.py`)
- Create draft roast
- Start roast (timestamp, stock deduction)
- End roast
- Add key timing events (FC, SC, Yellowing)
- Add temperature curve data
- Update roast details
- Delete roast (soft delete + stock restoration)
- Weight loss calculation
- Sync state endpoint
- Local CSV logging

### Review Operations (`test_reviews_api.py`)
- Add review to roast (JSON and form)
- Edit existing review
- Delete review
- Multiple reviews per roast
- Extraction method handling
- Score validation

### Temperature API (`test_temperature_api.py`)

- Temperature endpoint response format
- Error handling for unavailable sensor
- RoR calculation logic

**Note:** Temperature sensor tests are designed to pass whether the sensor is connected or not. When the sensor is unavailable, tests verify that the API gracefully returns error responses with the correct format.

### Application Boundaries (`test_app_factory.py`)

- Exact public route, method, and endpoint manifest
- `create_app()` local database name and sensor URL overrides
- Live-roast JSON bootstrap and JavaScript module entry

### Repository Policy (`test_file_size_policy.py`)

- Counts physical lines in tracked, human-authored Python, JavaScript, HTML,
  CSS, C++, header, and Markdown files
- Enforces the 1,000-line maximum with path and observed count failures
- Exempts generated tracker output, generated-notice files, vendored/minified
  assets, binaries, fonts, licenses, and lock files
- Requires oversized code to be split by responsibility and oversized
  documentation to be split by aspect with updated navigation

### Guarded Database Sync

- `test_sync_api.py` preserves RN-0015 timestamp-aware merge behavior.
- `test_database_sync.py` covers validation, sanitized preflight, both
  directions, sequential execution, and stop-on-failure behavior.
- `test_database_backup.py` verifies complete destination coverage, canonical
  Extended JSON BSON round trips, encoded collection names, byte counts,
  checksums, and incomplete backup handling.
- `test_database_sync_cli.py` covers dry-run side effects, both exact
  confirmations, cancellation policy, applied audit records, and untracked
  audit recovery.
- `test_database_sync_routes.py` verifies Settings audit-per-click behavior,
  read-only plans, sanitized failures, overlap prevention, and fail-closed
  historic routes.

These tests use in-memory fakes and temporary filesystem roots. They never run
an applied local/online mirror. Any configured live verification for sync must
use `--dry-run`; an applied run requires a separate explicit user request and
both run-specific confirmation tokens.

### Dedicated Browser E2E Harness

- `test_e2e_runtime.py` proves only the local `roastlogger_e2e` client is
  constructed, unsafe configuration is rejected, browser-created records are
  run-marked, updates retain markers, sync/global cleanup fail closed, and
  cleanup is run-scoped.
- `test_virtual_sensor.py` contract-tests all deterministic scenarios and
  representative retry/fault/recovery behavior through RoastLogger APIs.
- `test_api_contracts.py` covers label assets/preferences, database settings,
  rendered pages, malformed identifiers, missing records, and payload errors.
- `tests/e2e/README.md` is the Codex in-app-browser runbook.

Start and cleanup commands:

```bash
uv run python -m tests.e2e.manage start --run-id <unique-run-id>
uv run python -m tests.e2e.manage cleanup --run-id <unique-run-id>
```

Start runs in the foreground and binds the app and virtual sensor only to
loopback. Artifacts, runtime state, and E2E logs are ignored. Cleanup refuses
any database except `roastlogger_e2e`, deletes selected-run roasts before
beans, removes only their two CSV forms, and verifies zero matching records.

## Test Data Management

### Identification

All test data is marked with `test_data: True` field in MongoDB documents.
This allows easy identification and cleanup.

### Automatic Cleanup

Tests automatically clean up their data via pytest fixtures.
A session-scoped fixture also runs after all tests to clean any orphaned data.

### Manual Cleanup

If tests fail unexpectedly and leave orphaned data:

```bash
# Show count of test data
python tests/cleanup_test_data.py --count

# Delete all test data (with confirmation)
python tests/cleanup_test_data.py

# Delete without confirmation
python tests/cleanup_test_data.py --force
```

### From Python

```python
from tests.cleanup_test_data import cleanup_all_test_data, show_test_data_count

# Show counts
show_test_data_count()

# Clean up
results = cleanup_all_test_data()
print(f"Deleted {results['beans_deleted']} beans, {results['roasts_deleted']} roasts")
```

## Database Safety

- Existing API regression fixtures run only against the local database.
- Guarded-sync tests use in-memory fakes and temporary backup/audit roots.
- The `DEFAULT_DB` environment variable is set to `local` in conftest.py
- Never run tests against the production/online database.
- Never use an applied mirror as test setup, verification, or cleanup.

## Fixtures

Common fixtures in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `client` | Flask test client |
| `app` | Default application configured for API regression tests |
| `beans_collection` | Direct MongoDB beans collection access |
| `roasts_collection` | Direct MongoDB roasts collection access |
| `test_bean_data` | Sample bean form data |
| `created_test_bean` | Creates a bean, yields ID, cleans up after |
| `created_test_roast` | Creates roast with bean, yields IDs, cleans up |
| `started_test_roast` | Creates roast with start_time set |

## Adding New Tests

1. Create test file in `tests/` directory with `test_` prefix
2. Import fixtures from conftest.py
3. Mark any created documents with `test_data: True`
4. Use fixtures that auto-cleanup, or clean up in test teardown

Example:

```python
def test_my_feature(client, beans_collection):
    # Create test data
    bean_doc = {
        'name': 'Test Bean',
        'test_data': True,  # Mark as test data!
        # ... other fields
    }
    result = beans_collection.insert_one(bean_doc)

    try:
        # Test your feature
        response = client.get(f'/api/beans/{result.inserted_id}')
        assert response.status_code == 200
    finally:
        # Clean up
        beans_collection.delete_one({'_id': result.inserted_id})
```

Or better, use the provided fixtures that handle cleanup automatically.

## Ticket-System Verification

The tracker has focused tests for metadata validation, epics and child filing,
human-decision blockers, deterministic generation, stale output detection, and
the offline dashboard:

```bash
uv run pytest tests/test_ticket_system.py
uv run python scripts/generate_issues_index.py --check
```

Open `docs/issues/overview.html` directly after dashboard changes and verify the
Next, Board, Directory, Dependencies, detail, filter, theme, desktop, and mobile
states.

The supported generator script remains
`.claude/skills/ticket-master/scripts/generate_issues_index.py`; it delegates
record parsing, validation, filing, Markdown rendering, and orchestration to
the internal `tracker/` package while preserving the script and import
compatibility surface.
