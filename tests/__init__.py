"""
RoastLogger API Test Suite

Test data management:
- All test data is marked with `test_data: True` field
- Tests run against local database only
- Cleanup happens automatically after test session
- Manual cleanup: python tests/cleanup_test_data.py

Running tests:
    pip install -e ".[test]"
    pytest

Running specific tests:
    pytest tests/test_beans_api.py
    pytest tests/test_roasts_api.py -k "test_create"
"""
