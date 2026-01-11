# API Test Suite

API-level tests for RoastLogger backend operations.

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
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/test_beans_api.py
pytest tests/test_roasts_api.py
pytest tests/test_reviews_api.py
pytest tests/test_temperature_api.py
```

Run specific test class or method:

```bash
pytest tests/test_beans_api.py::TestBeanCreate
pytest tests/test_beans_api.py::TestBeanCreate::test_create_bean_valid_data
```

Run tests matching a pattern:

```bash
pytest -k "stock"  # All tests with "stock" in name
pytest -k "create or delete"  # Tests with "create" or "delete"
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

- Tests **only** run against the local database
- The `DEFAULT_DB` environment variable is set to `local` in conftest.py
- Never run tests against production/online database

## Fixtures

Common fixtures in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `client` | Flask test client |
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
