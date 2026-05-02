"""
Test configuration and fixtures for RoastLogger API tests.

All test data is marked with `test_data: true` field for easy identification and cleanup.
Tests run against the local database only.
"""
import os
import sys
import pytest
from datetime import datetime
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables before importing app
os.environ['DEFAULT_DB'] = 'local'
os.environ['TEMP_SENSOR_URL'] = 'http://localhost:9999/temp'  # Non-existent URL for tests

from app import app as flask_app, db_local


# Test data marker - all test documents include this field
TEST_DATA_MARKER = {'test_data': True}


@pytest.fixture
def app():
    """Create Flask application configured for testing."""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
    })

    # Ensure we're using local DB
    with flask_app.test_request_context():
        from flask import session
        session['db_mode'] = 'local'

    yield flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create application context."""
    with app.app_context():
        yield


@pytest.fixture
def beans_collection():
    """Direct access to beans collection for test setup/teardown."""
    return db_local.beans


@pytest.fixture
def roasts_collection():
    """Direct access to roasts collection for test setup/teardown."""
    return db_local.roasts


@pytest.fixture
def test_bean_data():
    """Sample bean data for testing."""
    return {
        'name': 'Test Ethiopian Yirgacheffe',
        'origin': 'Ethiopia',
        'process': 'Washed',
        'supplier': 'Test Supplier',
        'purchase_date': '2024-01-15',
        'purchase_price_total': '45.00',
        'purchase_weight_grams': '1000',
        'stock_grams': '1000',
        'color': '#8B4513',
        'short_flavor_notes': 'Blueberry\nJasmine\nDark Chocolate',
        'notes': 'Test bean notes',
    }


@pytest.fixture
def created_test_bean(beans_collection, test_bean_data):
    """Create a test bean and return its ID. Cleaned up after test."""
    bean_doc = {
        'name': test_bean_data['name'],
        'origin': test_bean_data['origin'],
        'process': test_bean_data['process'],
        'supplier': test_bean_data['supplier'],
        'purchase_date': datetime.strptime(test_bean_data['purchase_date'], '%Y-%m-%d'),
        'purchase_price_total': Decimal128(test_bean_data['purchase_price_total']),
        'purchase_weight_grams': int(test_bean_data['purchase_weight_grams']),
        'stock_grams': int(test_bean_data['stock_grams']),
        'color': test_bean_data['color'],
        'short_flavor_notes': ['Blueberry', 'Jasmine', 'Dark Chocolate'],
        'notes': test_bean_data['notes'],
        'unit_price_per_kg': Decimal128('45.00'),
        'archived': False,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        **TEST_DATA_MARKER
    }

    result = beans_collection.insert_one(bean_doc)
    bean_id = result.inserted_id

    yield str(bean_id)

    # Cleanup
    beans_collection.delete_one({'_id': bean_id})


@pytest.fixture
def created_test_roast(roasts_collection, beans_collection, test_bean_data):
    """Create a test roast with associated bean. Cleaned up after test."""
    # First create a bean
    bean_doc = {
        'name': test_bean_data['name'],
        'origin': test_bean_data['origin'],
        'process': test_bean_data['process'],
        'supplier': test_bean_data['supplier'],
        'stock_grams': int(test_bean_data['stock_grams']),
        'archived': False,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        **TEST_DATA_MARKER
    }
    bean_result = beans_collection.insert_one(bean_doc)
    bean_id = bean_result.inserted_id

    # Create a roast
    roast_doc = {
        'title': 'Test Roast',
        'bean_id': bean_id,
        'roast_date': datetime.now(),
        'original_weight_grams': 200,
        'roaster': 'Freshroast SR800',
        'temp_measurement_method': 'K-Type Sensor V1',
        'key_timings': [],
        'temp_curve': [],
        'reviews': [],
        'archived': False,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        **TEST_DATA_MARKER
    }
    roast_result = roasts_collection.insert_one(roast_doc)
    roast_id = roast_result.inserted_id

    yield {
        'roast_id': str(roast_id),
        'bean_id': str(bean_id),
        'original_stock': int(test_bean_data['stock_grams'])
    }

    # Cleanup
    roasts_collection.delete_one({'_id': roast_id})
    beans_collection.delete_one({'_id': bean_id})


@pytest.fixture
def started_test_roast(roasts_collection, beans_collection, test_bean_data):
    """Create a started test roast (with start_time set). Cleaned up after test."""
    # First create a bean
    bean_doc = {
        'name': test_bean_data['name'],
        'origin': test_bean_data['origin'],
        'process': test_bean_data['process'],
        'supplier': test_bean_data['supplier'],
        'stock_grams': int(test_bean_data['stock_grams']),
        'archived': False,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        **TEST_DATA_MARKER
    }
    bean_result = beans_collection.insert_one(bean_doc)
    bean_id = bean_result.inserted_id

    # Create a started roast
    roast_doc = {
        'title': 'Test Started Roast',
        'bean_id': bean_id,
        'roast_date': datetime.now(),
        'roast_start_time': datetime.now(),
        'original_weight_grams': 200,
        'roaster': 'Freshroast SR800',
        'temp_measurement_method': 'K-Type Sensor V1',
        'key_timings': [],
        'temp_curve': [],
        'reviews': [],
        'archived': False,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        **TEST_DATA_MARKER
    }
    roast_result = roasts_collection.insert_one(roast_doc)
    roast_id = roast_result.inserted_id

    yield {
        'roast_id': str(roast_id),
        'bean_id': str(bean_id),
        'original_stock': int(test_bean_data['stock_grams'])
    }

    # Cleanup
    roasts_collection.delete_one({'_id': roast_id})
    beans_collection.delete_one({'_id': bean_id})


def cleanup_test_data():
    """
    Remove all test data from database.
    Call this function to clean up any orphaned test data.

    Usage:
        from tests.conftest import cleanup_test_data
        cleanup_test_data()
    """
    beans_deleted = db_local.beans.delete_many({'test_data': True}).deleted_count
    roasts_deleted = db_local.roasts.delete_many({'test_data': True}).deleted_count

    print(f"Cleaned up test data: {beans_deleted} beans, {roasts_deleted} roasts deleted")
    return {'beans_deleted': beans_deleted, 'roasts_deleted': roasts_deleted}


@pytest.fixture(scope='session', autouse=True)
def cleanup_after_all_tests():
    """Cleanup any remaining test data after all tests complete."""
    yield
    # After all tests, clean up any orphaned test data
    cleanup_test_data()


# Utility functions for test assertions
def get_test_bean_by_id(beans_collection, bean_id):
    """Get a bean by ID, ensuring it's test data."""
    return beans_collection.find_one({
        '_id': ObjectId(bean_id),
        'test_data': True
    })


def get_test_roast_by_id(roasts_collection, roast_id):
    """Get a roast by ID, ensuring it's test data."""
    return roasts_collection.find_one({
        '_id': ObjectId(roast_id),
        'test_data': True
    })
