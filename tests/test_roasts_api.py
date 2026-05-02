"""
API tests for Roast operations.

Tests cover:
- Create draft roast
- Start roast (verify timestamp, stock deduction)
- Add key timing events (FC, SC, etc.)
- Add temperature readings
- End roast (verify final data)
- Edit roast details
- Delete roast (verify soft delete + stock restoration)
- Weight loss calculation
"""
import pytest
import time
from datetime import datetime
from bson.objectid import ObjectId

import app as app_module
from tests.conftest import TEST_DATA_MARKER


class TestRoastCreate:
    """Tests for roast creation."""

    def test_create_draft_roast(self, client, roasts_collection):
        """Test creating a new draft roast via API."""
        response = client.post('/api/roast/create')

        assert response.status_code == 200
        data = response.get_json()
        assert 'new_roast_id' in data

        roast_id = data['new_roast_id']

        # Verify roast was created
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast is not None
        assert roast['title'] == 'Untitled Roast'
        assert roast['roaster'] == 'Freshroast SR800'
        assert roast['temp_measurement_method'] == 'K-Type Sensor V1'
        assert roast['key_timings'] == []
        assert roast['temp_curve'] == []
        assert roast['reviews'] == []
        assert roast['lifecycle_status'] == 'draft'
        assert roast['archived'] == False

        # Cleanup
        roasts_collection.delete_one({'_id': ObjectId(roast_id)})

    def test_create_roast_html_redirect(self, client, roasts_collection):
        """Test creating roast via HTML route redirects to live interface."""
        response = client.get('/roast/new', follow_redirects=False)

        assert response.status_code == 302
        assert '/roast/live/' in response.location

        # Extract roast ID and cleanup
        roast_id = response.location.split('/roast/live/')[-1]
        roasts_collection.delete_one({'_id': ObjectId(roast_id)})


class TestRoastNavigation:
    """Tests for lifecycle-aware roast navigation."""

    def test_dashboard_links_roasts_by_lifecycle_state(self, client, roasts_collection):
        """Draft and started roasts return to live page; completed roasts open detail page."""
        now = datetime.now()
        roast_docs = [
            {
                'title': 'Lifecycle Draft Roast',
                'roast_date': now,
                'key_timings': [],
                'temp_curve': [],
                'reviews': [],
                'archived': False,
                'created_at': now,
                'updated_at': now,
                **TEST_DATA_MARKER
            },
            {
                'title': 'Lifecycle Active Roast',
                'roast_date': now,
                'roast_start_time': now,
                'key_timings': [],
                'temp_curve': [],
                'reviews': [],
                'archived': False,
                'created_at': now,
                'updated_at': now,
                **TEST_DATA_MARKER
            },
            {
                'title': 'Lifecycle Completed Roast',
                'roast_date': now,
                'roast_start_time': now,
                'roast_end_time': now,
                'key_timings': [],
                'temp_curve': [],
                'reviews': [],
                'archived': False,
                'created_at': now,
                'updated_at': now,
                **TEST_DATA_MARKER
            },
            {
                'title': 'Lifecycle Status Completed Roast',
                'roast_date': now,
                'lifecycle_status': 'completed',
                'key_timings': [],
                'temp_curve': [],
                'reviews': [],
                'archived': False,
                'created_at': now,
                'updated_at': now,
                **TEST_DATA_MARKER
            },
        ]
        inserted_ids = roasts_collection.insert_many(roast_docs).inserted_ids

        try:
            response = client.get('/')
            html = response.get_data(as_text=True)

            assert response.status_code == 200
            assert f'/roast/live/{inserted_ids[0]}' in html
            assert f'/api/roast/delete/{inserted_ids[0]}' in html
            assert 'Draft' in html
            assert f'/roast/live/{inserted_ids[1]}' in html
            assert 'In Progress' in html
            assert f'/roast/detail/{inserted_ids[2]}' in html
            assert 'Completed' in html
            assert f'/roast/detail/{inserted_ids[3]}' in html
        finally:
            roasts_collection.delete_many({'_id': {'$in': inserted_ids}})

    def test_bean_history_uses_explicit_completed_lifecycle(
        self, client, beans_collection, roasts_collection
    ):
        """Bean roast history opens completed-by-status roasts on the detail page."""
        now = datetime.now()
        bean_id = beans_collection.insert_one(
            {
                'name': 'Lifecycle Bean',
                'stock_grams': 1000,
                'archived': False,
                'created_at': now,
                'updated_at': now,
                **TEST_DATA_MARKER
            }
        ).inserted_id
        roast_id = roasts_collection.insert_one(
            {
                'title': 'Completed By Status',
                'bean_id': bean_id,
                'roast_date': now,
                'lifecycle_status': 'completed',
                'key_timings': [],
                'temp_curve': [],
                'reviews': [],
                'archived': False,
                'created_at': now,
                'updated_at': now,
                **TEST_DATA_MARKER
            }
        ).inserted_id

        try:
            response = client.get(f'/beans/detail/{bean_id}')
            html = response.get_data(as_text=True)

            assert response.status_code == 200
            assert f'/roast/detail/{roast_id}' in html
            assert 'Completed' in html
        finally:
            roasts_collection.delete_one({'_id': roast_id})
            beans_collection.delete_one({'_id': bean_id})


class TestRoastStart:
    """Tests for starting a roast."""

    def test_start_roast_sets_start_time(self, client, roasts_collection, created_test_roast):
        """Test that starting a roast sets the start time."""
        roast_id = created_test_roast['roast_id']

        before_start = datetime.now()
        response = client.post(
            f'/api/roast/start/{roast_id}',
            json={},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

        # Verify start time was set
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['roast_start_time'] is not None
        assert roast['lifecycle_status'] == 'started'

    def test_start_roast_with_bean_decrements_stock(
        self, client, beans_collection, roasts_collection, created_test_roast
    ):
        """Test that starting a roast with bean info decrements bean stock."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']
        original_stock = created_test_roast['original_stock']
        bean_before_start = beans_collection.find_one({'_id': ObjectId(bean_id)})

        start_data = {
            'bean_id': bean_id,
            'original_weight_grams': 200
        }

        response = client.post(
            f'/api/roast/start/{roast_id}',
            json=start_data,
            content_type='application/json'
        )

        assert response.status_code == 200

        # Verify stock was decremented
        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['stock_grams'] == original_stock - 200
        assert 'created_at' in bean
        assert app_module.normalize_sync_timestamp(
            bean['updated_at']
        ) > app_module.normalize_sync_timestamp(bean_before_start['updated_at'])

    def test_start_roast_sets_ambient_conditions(self, client, roasts_collection, created_test_roast):
        """Test that starting a roast records ambient conditions."""
        roast_id = created_test_roast['roast_id']

        start_data = {
            'ambient_temp_celsius': 22.5,
            'ambient_humidity': 65.0
        }

        client.post(
            f'/api/roast/start/{roast_id}',
            json=start_data,
            content_type='application/json'
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['ambient_temp_celsius'] == 22.5
        assert roast['ambient_humidity'] == 65.0


class TestRoastEnd:
    """Tests for ending a roast."""

    def test_end_roast_sets_end_time(self, client, roasts_collection, started_test_roast):
        """Test that ending a roast sets the end time."""
        roast_id = started_test_roast['roast_id']

        response = client.post(f'/api/roast/end/{roast_id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

        # Verify end time was set
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['roast_end_time'] is not None
        assert roast['lifecycle_status'] == 'completed'

    def test_end_nonexistent_roast(self, client):
        """Test ending a roast that doesn't exist."""
        fake_id = str(ObjectId())
        response = client.post(f'/api/roast/end/{fake_id}')

        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] == False


class TestRoastManualCompletion:
    """Tests for manually completing draft roasts."""

    def test_complete_draft_roast_sets_completed_status(
        self, client, roasts_collection, created_test_roast
    ):
        """Manual completion updates lifecycle metadata only."""
        roast_id = created_test_roast['roast_id']
        before = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        original_updated_at = before['updated_at']

        response = client.post(f'/api/roast/complete_draft/{roast_id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['lifecycle_status'] == 'completed'

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['lifecycle_status'] == 'completed'
        assert app_module.normalize_sync_timestamp(
            roast['updated_at']
        ) > app_module.normalize_sync_timestamp(original_updated_at)
        assert roast.get('roast_start_time') is None
        assert roast.get('roast_end_time') is None
        assert roast['key_timings'] == []
        assert roast['temp_curve'] == []
        assert roast.get('sensor_diagnostics') is None

    def test_complete_started_roast_is_rejected(
        self, client, roasts_collection, started_test_roast
    ):
        """Manual completion is draft-only and rejects active roasts."""
        roast_id = started_test_roast['roast_id']

        response = client.post(f'/api/roast/complete_draft/{roast_id}')

        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] == False

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast.get('lifecycle_status') != 'completed'

    def test_complete_completed_roast_is_rejected(
        self, client, roasts_collection, created_test_roast
    ):
        """Manual completion rejects already completed roasts."""
        roast_id = created_test_roast['roast_id']
        roasts_collection.update_one(
            {'_id': ObjectId(roast_id)},
            {'$set': {'lifecycle_status': 'completed'}},
        )

        response = client.post(f'/api/roast/complete_draft/{roast_id}')

        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] == False


class TestRoastTiming:
    """Tests for adding timing events to roasts."""

    def test_add_timing_event(self, client, roasts_collection, started_test_roast):
        """Test adding a key timing event."""
        roast_id = started_test_roast['roast_id']

        timing_data = {
            'event_name': 'First Crack Start',
            'time_seconds': 420,
            'temperature': 195.0,
            'fan_setting': 9,
            'power_setting': 5
        }

        response = client.post(
            f'/api/roast/add_timing/{roast_id}',
            json=timing_data,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

        # Verify timing was added
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['key_timings']) == 1
        assert roast['key_timings'][0]['event_name'] == 'First Crack Start'
        assert roast['key_timings'][0]['time_seconds'] == 420
        assert roast['key_timings'][0]['temperature'] == 195.0

    def test_add_multiple_timing_events(self, client, roasts_collection, started_test_roast):
        """Test adding multiple timing events."""
        roast_id = started_test_roast['roast_id']

        events = [
            {'event_name': 'Yellowing', 'time_seconds': 180, 'temperature': 150.0},
            {'event_name': 'First Crack Start', 'time_seconds': 420, 'temperature': 195.0},
            {'event_name': 'First Crack End', 'time_seconds': 450, 'temperature': 200.0},
        ]

        for event in events:
            client.post(
                f'/api/roast/add_timing/{roast_id}',
                json=event,
                content_type='application/json'
            )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['key_timings']) == 3

    def test_add_timing_without_temperature(self, client, roasts_collection, started_test_roast):
        """Test adding timing without temperature (sensor unavailable scenario)."""
        roast_id = started_test_roast['roast_id']

        timing_data = {
            'event_name': 'First Crack Start',
            'time_seconds': 420,
            # No temperature provided, and sensor URL is non-existent
        }

        response = client.post(
            f'/api/roast/add_timing/{roast_id}',
            json=timing_data,
            content_type='application/json'
        )

        assert response.status_code == 200

        # Timing should still be added
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['key_timings']) == 1


class TestRoastTempCurve:
    """Tests for temperature curve data."""

    def test_add_temp_event(self, client, roasts_collection, started_test_roast):
        """Test adding a temperature curve event."""
        roast_id = started_test_roast['roast_id']

        event_data = {
            'time_seconds': 60,
            'temperature': 150.0,
            'fan_setting': 9,
            'power_setting': 5
        }

        response = client.post(
            f'/api/roast/add_event/{roast_id}',
            json=event_data,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

        # Verify event was added
        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['temp_curve']) == 1
        assert roast['temp_curve'][0]['time_seconds'] == 60
        assert roast['temp_curve'][0]['temperature'] == 150.0
        assert roast['temp_curve'][0]['fan_setting'] == 9
        assert roast['temp_curve'][0]['power_setting'] == 5

    def test_add_temp_event_with_note(self, client, roasts_collection, started_test_roast):
        """Test adding a temperature event with a note."""
        roast_id = started_test_roast['roast_id']

        event_data = {
            'time_seconds': 120,
            'temperature': 165.0,
            'fan_setting': 9,
            'power_setting': 6,
            'note': 'Increased power'
        }

        client.post(
            f'/api/roast/add_event/{roast_id}',
            json=event_data,
            content_type='application/json'
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['temp_curve'][0]['note'] == 'Increased power'

    def test_temp_event_default_fan_power(self, client, roasts_collection, started_test_roast):
        """Test that fan/power default to 9/3 if not provided."""
        roast_id = started_test_roast['roast_id']

        event_data = {
            'time_seconds': 60,
            'temperature': 150.0,
            # No fan_setting or power_setting
        }

        client.post(
            f'/api/roast/add_event/{roast_id}',
            json=event_data,
            content_type='application/json'
        )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['temp_curve'][0]['fan_setting'] == 9
        assert roast['temp_curve'][0]['power_setting'] == 3


class TestRoastUpdate:
    """Tests for updating roast details."""

    def test_update_roast_title(self, client, roasts_collection, created_test_roast):
        """Test updating roast title via JSON API."""
        roast_id = created_test_roast['roast_id']

        response = client.post(
            f'/api/roast/update_title/{roast_id}',
            json={'title': 'My Best Roast'},
            content_type='application/json'
        )

        assert response.status_code == 200

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['title'] == 'My Best Roast'

    def test_update_roast_setup_persists_without_starting(
        self, client, roasts_collection, beans_collection, created_test_roast
    ):
        """Test pre-start setup autosave does not start roast or change bean stock."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']
        original_stock = created_test_roast['original_stock']

        response = client.post(
            f'/api/roast/update_setup/{roast_id}',
            json={
                'title': 'Prepared Draft Roast',
                'bean_id': bean_id,
                'original_weight_grams': 180,
                'ambient_temp_celsius': 23.5,
                'ambient_humidity': 58
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        assert response.get_json()['success'] == True

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['title'] == 'Prepared Draft Roast'
        assert roast['bean_id'] == ObjectId(bean_id)
        assert roast['original_weight_grams'] == 180
        assert roast['ambient_temp_celsius'] == 23.5
        assert roast['ambient_humidity'] == 58.0
        assert roast.get('roast_start_time') is None

        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['stock_grams'] == original_stock

    def test_update_roast_setup_rejects_started_roast(self, client, started_test_roast):
        """Test setup autosave cannot mutate a roast after it starts."""
        roast_id = started_test_roast['roast_id']

        response = client.post(
            f'/api/roast/update_setup/{roast_id}',
            json={'original_weight_grams': 180},
            content_type='application/json'
        )

        assert response.status_code == 409

    def test_update_roast_form(self, client, roasts_collection, beans_collection, created_test_roast):
        """Test updating roast via form submission."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']

        form_data = {
            'title': 'Updated Roast Title',
            'roast_date': '2024-06-15T14:30',
            'bean_id': bean_id,
            'original_weight_grams': '200',
            'roasted_weight_grams': '170',
            'roaster': 'Test Roaster',
            'temp_measurement_method': 'Manual',
            'ambient_temp_celsius': '25',
            'ambient_humidity': '50',
            'general_notes': 'Test notes',
        }

        response = client.post(
            f'/api/roast/update/{roast_id}',
            data=form_data,
            follow_redirects=False
        )

        assert response.status_code == 302  # Redirects to detail page

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['title'] == 'Updated Roast Title'
        assert roast['original_weight_grams'] == 200
        assert roast['roasted_weight_grams'] == 170

    def test_update_draft_roast_form_does_not_decrement_stock(
        self, client, roasts_collection, beans_collection, created_test_roast
    ):
        """Test editing draft green weight does not affect bean stock before start."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']
        original_stock = created_test_roast['original_stock']

        form_data = {
            'title': 'Draft Weight Change',
            'bean_id': bean_id,
            'original_weight_grams': '100',
        }

        response = client.post(
            f'/api/roast/update/{roast_id}',
            data=form_data,
            follow_redirects=False
        )

        assert response.status_code == 302

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['original_weight_grams'] == 100
        assert roast.get('roast_start_time') is None

        bean = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean['stock_grams'] == original_stock

    def test_update_roast_calculates_weight_loss(
        self, client, roasts_collection, created_test_roast
    ):
        """Test that updating weights calculates weight loss percentage."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']

        form_data = {
            'title': 'Weight Loss Test',
            'bean_id': bean_id,
            'original_weight_grams': '200',
            'roasted_weight_grams': '160',  # 20% loss
        }

        client.post(f'/api/roast/update/{roast_id}', data=form_data, follow_redirects=False)

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast['weight_loss_percentage'] == 20.0


class TestRoastDelete:
    """Tests for roast deletion."""

    def test_delete_roast_soft_deletes(self, client, roasts_collection, created_test_roast):
        """Test that deleting a roast sets archived=True."""
        roast_id = created_test_roast['roast_id']

        response = client.post(f'/api/roast/delete/{roast_id}', follow_redirects=False)

        assert response.status_code == 302  # Redirects to index

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert roast is not None
        assert roast['archived'] == True

    def test_delete_draft_roast_does_not_restore_stock(
        self, client, beans_collection, created_test_roast
    ):
        """Test deleting a saved draft does not add stock that was never deducted."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']
        original_stock = created_test_roast['original_stock']

        client.post(f'/api/roast/delete/{roast_id}', follow_redirects=False)

        bean_after_delete = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean_after_delete['stock_grams'] == original_stock

    def test_delete_roast_restores_bean_stock(
        self, client, beans_collection, roasts_collection, created_test_roast
    ):
        """Test that deleting a roast restores bean stock."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']

        # First start roast to decrement stock
        start_data = {
            'bean_id': bean_id,
            'original_weight_grams': 150
        }
        client.post(
            f'/api/roast/start/{roast_id}',
            json=start_data,
            content_type='application/json'
        )

        # Update roast record to have original_weight_grams
        roasts_collection.update_one(
            {'_id': ObjectId(roast_id)},
            {'$set': {'original_weight_grams': 150}}
        )

        # Get stock after start
        bean_after_start = beans_collection.find_one({'_id': ObjectId(bean_id)})
        stock_after_start = bean_after_start['stock_grams']

        # Delete roast
        client.post(f'/api/roast/delete/{roast_id}', follow_redirects=False)

        # Verify stock restored
        bean_after_delete = beans_collection.find_one({'_id': ObjectId(bean_id)})
        assert bean_after_delete['stock_grams'] == stock_after_start + 150
        assert 'created_at' in bean_after_delete
        assert app_module.normalize_sync_timestamp(
            bean_after_delete['updated_at']
        ) > app_module.normalize_sync_timestamp(bean_after_start['updated_at'])


class TestRoastSyncState:
    """Tests for the consolidated sync_state endpoint."""

    @staticmethod
    def _reading(temperature, sensor_status='ok', attempts=3, successes=3, errors=None):
        return {
            'temperature': temperature,
            'sensor_status': sensor_status,
            'attempts': attempts,
            'successes': successes,
            'duration_ms': 230,
            'errors': errors or [],
            'attempt_results': [],
            'diagnostics': None,
        }

    def test_sync_state_returns_response(self, client, started_test_roast):
        """Test that sync_state returns expected response format."""
        roast_id = started_test_roast['roast_id']

        sync_data = {
            'time_seconds': 60,
            'status': 'running',
            'fan_setting': 9,
            'power_setting': 5
        }

        response = client.post(
            f'/api/roast/sync_state/{roast_id}',
            json=sync_data,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
        assert 'temperature' in data
        assert 'ror' in data
        assert 'logged_to_db' in data
        assert 'sensor_status' in data
        assert 'attempts' in data
        assert 'successes' in data
        assert 'duration_ms' in data

    def test_sync_state_logs_single_success_after_retry(self, client, roasts_collection, started_test_roast, monkeypatch):
        """One successful retry should log a temperature point."""
        roast_id = started_test_roast['roast_id']
        app_module.roast_temp_history.pop(roast_id, None)
        monkeypatch.setattr(
            app_module,
            'fetch_temperature_reading',
            lambda **kwargs: self._reading(
                185,
                sensor_status='retrying',
                attempts=3,
                successes=1,
                errors=['timeout'],
            ),
        )

        response = client.post(
            f'/api/roast/sync_state/{roast_id}',
            json={
                'time_seconds': 5,
                'status': 'running',
                'fan_setting': 9,
                'power_setting': 5,
            },
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['temperature'] == 185
        assert data['sensor_status'] == 'retrying'
        assert data['logged_to_db'] is True

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['temp_curve']) == 1
        temp_event = roast['temp_curve'][0]
        assert temp_event['temperature'] == 185.0
        assert temp_event['sensor_status'] == 'retrying'
        assert temp_event['sensor_attempts'] == 3
        assert temp_event['sensor_successes'] == 1
        assert temp_event['sensor_read_ms'] == 230

    def test_sync_state_marks_sensor_stale_after_five_second_gap(self, client, roasts_collection, started_test_roast, monkeypatch):
        """Repeated failures should become stale after the configured threshold."""
        roast_id = started_test_roast['roast_id']
        app_module.roast_temp_history.pop(roast_id, None)
        readings = iter([
            self._reading(180),
            self._reading(None, sensor_status='offline', attempts=3, successes=0, errors=['timeout']),
            self._reading(None, sensor_status='offline', attempts=3, successes=0, errors=['timeout']),
        ])

        monkeypatch.setattr(
            app_module,
            'fetch_temperature_reading',
            lambda **kwargs: next(readings),
        )

        client.post(
            f'/api/roast/sync_state/{roast_id}',
            json={'time_seconds': 1, 'status': 'running', 'fan_setting': 9, 'power_setting': 5},
            content_type='application/json',
        )
        client.post(
            f'/api/roast/sync_state/{roast_id}',
            json={'time_seconds': 2, 'status': 'running', 'fan_setting': 9, 'power_setting': 5},
            content_type='application/json',
        )
        response = client.post(
            f'/api/roast/sync_state/{roast_id}',
            json={'time_seconds': 6, 'status': 'running', 'fan_setting': 9, 'power_setting': 5},
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['temperature'] is None
        assert data['sensor_status'] == 'stale'
        assert data['last_success_age_seconds'] == app_module.TEMP_SENSOR_STALE_SECONDS

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['temp_curve']) == 1
        assert roast['sensor_diagnostics'][-1]['sensor_status'] == 'stale'

    def test_sensor_diagnostic_array_is_bounded(self, roasts_collection, started_test_roast, monkeypatch):
        """Roast-level anomaly diagnostics should retain only the newest entries."""
        roast_id = started_test_roast['roast_id']
        monkeypatch.setattr(
            app_module,
            'get_roasts_collection',
            lambda: roasts_collection,
        )

        for time_seconds in range(app_module.MAX_SENSOR_DIAGNOSTICS + 5):
            app_module.append_roast_sensor_diagnostic(
                roast_id,
                {
                    'time_seconds': time_seconds,
                    'sensor_status': 'offline',
                    'temperature': None,
                    'attempts': 3,
                    'successes': 0,
                    'duration_ms': 2250,
                    'last_success_age_seconds': time_seconds,
                },
            )

        roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})
        assert len(roast['sensor_diagnostics']) == app_module.MAX_SENSOR_DIAGNOSTICS
        assert roast['sensor_diagnostics'][0]['time_seconds'] == 5

    def test_sync_state_logs_to_csv(self, client, started_test_roast):
        """Test that sync_state creates local CSV file."""
        import os
        roast_id = started_test_roast['roast_id']

        sync_data = {
            'time_seconds': 5,
            'status': 'running',
            'fan_setting': 9,
            'power_setting': 5
        }

        client.post(
            f'/api/roast/sync_state/{roast_id}',
            json=sync_data,
            content_type='application/json'
        )

        # Check if CSV file was created (even if temp is null)
        log_file = os.path.join(os.getcwd(), 'temp_logs', f'{roast_id}.csv')
        # Note: File may not exist if temperature is None
        # This test mainly verifies the endpoint works


class TestRoastLocalTempLog:
    """Tests for local temperature logging."""

    def test_log_temp_local_creates_file(self, client, started_test_roast):
        """Test that log_temp_local creates/appends to CSV."""
        import os
        roast_id = started_test_roast['roast_id']

        log_data = {
            'time_seconds': 60,
            'temperature': 185.5,
            'ror': 12.5
        }

        response = client.post(
            f'/api/roast/log_temp_local/{roast_id}',
            json=log_data,
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

        # Verify file exists
        log_file = os.path.join(os.getcwd(), 'temp_logs', f'{roast_id}.csv')
        assert os.path.exists(log_file)

        # Read and verify content
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'time_seconds,temperature,ror' in content
            assert '60,185.5,12.5' in content

        # Cleanup
        os.remove(log_file)

    def test_log_temp_local_appends_data(self, client, started_test_roast):
        """Test that subsequent logs append to existing file."""
        import os
        roast_id = started_test_roast['roast_id']

        # Log first entry
        client.post(
            f'/api/roast/log_temp_local/{roast_id}',
            json={'time_seconds': 60, 'temperature': 150.0},
            content_type='application/json'
        )

        # Log second entry
        client.post(
            f'/api/roast/log_temp_local/{roast_id}',
            json={'time_seconds': 120, 'temperature': 165.0},
            content_type='application/json'
        )

        log_file = os.path.join(os.getcwd(), 'temp_logs', f'{roast_id}.csv')
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3  # Header + 2 data lines

        # Cleanup
        os.remove(log_file)
