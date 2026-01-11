# [RESOLVED] API Testing Framework

**Status:** RESOLVED
**Created:** 2026-01-11
**Resolved:** 2026-01-11
**Priority:** HIGH

## Description

Added API-level tests for backend operations to ensure data integrity and business logic correctness.

## What Was Implemented

### Test Framework Setup
- Added pytest and pytest-flask to `pyproject.toml`
- Created `tests/conftest.py` with fixtures for Flask client, database access, and test data
- Created comprehensive test documentation in `tests/README.md`

### Test Coverage (58 tests total)

#### Bean Operations (`test_beans_api.py` - 14 tests)
- Create bean with valid/invalid data
- Edit bean details
- Delete bean (soft delete verification)
- Stock management (decrement on roast, restore on delete)
- Unit price calculation
- Form validation and data handling

#### Roast Operations (`test_roasts_api.py` - 22 tests)
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

#### Review Operations (`test_reviews_api.py` - 14 tests)
- Add review to roast (JSON and form)
- Edit existing review
- Delete review
- Multiple reviews per roast
- Extraction method handling
- Score validation

#### Temperature API (`test_temperature_api.py` - 8 tests)
- Temperature endpoint response format
- Error handling for unavailable sensor
- Sensor URL settings API
- RoR calculation logic

### Test Data Management
- All test data marked with `test_data: True` field
- Tests run only against local database
- Automatic cleanup after test session
- Manual cleanup script: `python tests/cleanup_test_data.py`

### Additional Improvements
- Fixed Flask 3.0 compatibility issue with `request.get_json(silent=True)`
- Added temperature sensor URL configuration via settings page
- Updated CLAUDE.md with testing instructions for AI

## Running Tests

```bash
# Install dependencies
uv pip install pytest pytest-flask

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_beans_api.py
```

## Files Added/Modified

### Added
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_beans_api.py`
- `tests/test_roasts_api.py`
- `tests/test_reviews_api.py`
- `tests/test_temperature_api.py`
- `tests/cleanup_test_data.py`
- `tests/README.md`

### Modified
- `pyproject.toml` - Added test dependencies and pytest config
- `app.py` - Fixed `get_json(silent=True)` for Flask 3.0, added sensor URL settings
- `templates/base.html` - Added sensor URL settings UI
- `static/css/style.css` - Added sensor URL container styles
- `CLAUDE.md` - Added testing instructions

## Success Criteria Met

- [x] Test coverage for all API endpoints
- [x] Verify database CRUD operations work correctly
- [x] Stock calculations tested (deduction/restoration)
- [x] RoR calculation accuracy verified
- [x] Data validation rules enforced
- [x] Soft delete behavior confirmed
- [x] Test data clearly labeled and easy to clean up
- [x] Tests run only on local database
- [x] Documentation added for running tests
