# API Test Suite

API-level tests for RoastLogger backend operations.

## When to Run Tests

Run the test suite in these situations:

1. **After changes to API endpoints, database operations, or business logic** — any change that could regress backend behaviour.
2. **After adding new features** — write tests alongside the implementation, not after.
3. **Before committing** — verify the suite passes before finalising changes.
4. **When explicitly requested** — running specific tests or the full suite on demand.
5. **After ticket-system changes** — run the tracker tests and stale-generation check after changing its schema, templates, generator, dashboard, or skill.

For documentation-only changes, running the API suite is usually unnecessary.
UI and CSS changes follow the Testing Impact policy below: visible behavior
uses browser verification proportional to its risk and reach.

## Testing Impact Policy

`tests/README.md` is the canonical automated test inventory. The durable UI
regression checklist lives in `tests/e2e/README.md`; do not copy either
changing list into ticket-master instructions or individual tickets.

Every active ticket uses
`.claude/skills/ticket-master/TESTING_WORKFLOW.md` to record:

- the change classification;
- browser verification level `none`, `targeted`, or `full`;
- exact automated tests to add or update;
- exact browser scenarios to add or update;
- required commands and evidence; and
- a concrete reason for any omitted coverage.

Small low-risk visual-only fixes may use browser level `none` with a concrete
reason and do not require a browser task or E2E checklist update. Focused
layout or interaction changes use `targeted` and update the relevant scenario.
Cross-screen workflows and behavioral changes to live roasting, sensors,
inventory deduction, Settings, or sync UI use `full`. Browser checks supplement
focused automated tests and `uv run pytest`; they do not replace them.

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
uv run pytest tests/test_database_sync_web.py
uv run pytest tests/test_e2e_runtime.py
uv run pytest tests/test_virtual_sensor.py
uv run pytest tests/test_api_contracts.py
uv run pytest tests/test_design_contracts.py
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

## Automated Test Module Inventory

| Module | Primary coverage |
| --- | --- |
| `test_api_contracts.py` | Labels, preferences, Settings, rendered stock-history and Beans-list remaining-meter states, identifiers, and payload failures |
| `test_app_factory.py` | Route manifest, configuration boundaries, and live-roast module entry |
| `test_beans_api.py` | Bean CRUD, stock, labels, pricing, and validation |
| `test_database_backup.py` | Complete backups, BSON round trips, and incomplete-backup safety |
| `test_database_sync.py` | Sync validation, read-only preflight, direction, and conflicts |
| `test_database_sync_cli.py` | Confirmations, cancellation, backups, and audit behavior |
| `test_database_sync_routes.py` | Audited Settings preflight, overlap prevention, and fail-closed routes |
| `test_database_sync_web.py` | Phased backup/apply/cancel state, resume, endpoint-drift rejection, exclusive claims, replay, and recovery |
| `test_design_contracts.py` | Quiet Compact contrast, font scope, density, reduced motion, and navigation transition contracts |
| `test_datetime_formatting.py` | UTC and operator-timezone formatting |
| `test_e2e_runtime.py` | Isolated database, run markers, cleanup, and online exclusion |
| `test_file_size_policy.py` | Tracked-file 1,000-line policy |
| `test_reviews_api.py` | Review CRUD and validation |
| `test_roasts_api.py` | Roast lifecycle, events, temperature, stock, and weight loss |
| `test_settings_sheet_contracts.py` | Settings dialog semantics, section tabs, focus/state behavior, and responsive sheet geometry |
| `test_sync_api.py` | Timestamp-aware document synchronization, including embedded bean stock history |
| `test_temperature_api.py` | Temperature endpoints, timeouts, settings, and RoR |
| `test_ticket_system.py` | Tracker validation, policy, generation, and dashboard |
| `test_virtual_sensor.py` | Deterministic sensor scenarios and recovery |

## Test Coverage

### Bean Operations (`test_beans_api.py`)
- Create bean with valid/invalid data
- Edit bean details
- Delete bean (soft delete verification)
- Stock deduction/restoration and atomic positive/negative set-to-zero history
- Unit price calculation
- Form validation and data handling

### Rendered Bean Contracts (`test_api_contracts.py`)

- Beans-list stock pills retain signed, uncapped gram values and raw-stock
  sorting.
- Remaining meters expose clamped 0–100 values for positive integer purchase
  baselines and omit the progressbar for missing or invalid baselines.
- Existing out-of-stock labels and visibility remain stable.

### Quiet Compact Design Contracts (`test_design_contracts.py`)

- Secondary and tertiary text colors meet WCAG AA on documented light and
  dark surfaces.
- Global and label-only font resources stay route-scoped without duplicate
  token imports.
- Management and live-roast target sizes remain separate at 44px and 54px.
- Flat grouping, motion tokens, and reduced-motion overrides remain present.
- Roasts/Beans navigation retains named progressive transitions, native link
  semantics, and the live-roast content opt-out.

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
  direct peer/host, same-origin JSON, distinct preflight audits, phased route
  payloads, sanitized failures, and fail-closed historic routes.
- `test_database_sync_web.py` verifies exact one-use preview confirmation,
  complete-backup verification before apply, zero pre-apply writes, atomic
  resumable state, single-run claims, competing previews, cancellation, replay
  rejection, corruption recovery, terminal audit behavior, and both directions.
- `test_database_sync_cli.py` also locks the original prompt text/order and exit
  behavior after the shared runner was separated into phases.

These tests use in-memory fakes and temporary filesystem roots. They never run
an applied local/online mirror. Any configured live verification for sync must
use `--dry-run`; an applied run requires a separate explicit user request and
both run-specific confirmation tokens.

Run the focused guarded-sync contract with:

```bash
uv run pytest \
  tests/test_database_sync_web.py \
  tests/test_database_sync_routes.py \
  tests/test_database_sync_cli.py \
  tests/test_database_sync.py \
  tests/test_database_backup.py \
  tests/test_sync_api.py \
  tests/test_app_factory.py \
  tests/test_e2e_runtime.py \
  tests/test_settings_sheet_contracts.py \
  tests/test_api_contracts.py \
  tests/test_file_size_policy.py
```

### Dedicated Browser E2E Harness

- `test_e2e_runtime.py` proves only the local `roastlogger_e2e` client is
  constructed, unsafe configuration is rejected, ordinary sync/global cleanup
  fail closed, the explicit sync fake writes only ignored artifact data without
  database access, browser-created records are run-marked, and cleanup is
  run-scoped.
- `test_virtual_sensor.py` contract-tests all deterministic scenarios and
  representative retry/fault/recovery behavior through RoastLogger APIs.
- `test_api_contracts.py` covers label assets/preferences, database settings,
  rendered pages, malformed identifiers, missing records, and payload errors.
- `test_settings_sheet_contracts.py` locks the rendered dialog/tab
  relationships, session section restoration, focus containment and return,
  hidden-panel exclusion, body scroll lock, viewport geometry, mobile
  full-screen fallback, and reduced-motion contract.
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

Add `--sync-fake` only for the guarded Settings browser scenario. The app
server then injects `tests.e2e.sync_fake.E2ESyncExecutor`; the ordinary harness
has no applied-sync executor. The fake refuses non-artifact roots, never
constructs or uses an online MongoDB client, and records every simulated phase
with `database_access: false`.

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
5. For browser level `targeted` or `full`, add or update the durable browser
   scenario in `tests/e2e/README.md`

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
the offline dashboard. It also enforces `testing_policy: v1`, complete Testing
Impact fields, checked testing acceptance on completed policy tickets, valid
browser levels, proportional omission for small visual fixes, and browser
scenarios/evidence for interaction and workflow classifications:

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
