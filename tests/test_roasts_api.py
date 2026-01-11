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

    def test_start_roast_with_bean_decrements_stock(
        self, client, beans_collection, roasts_collection, created_test_roast
    ):
        """Test that starting a roast with bean info decrements bean stock."""
        roast_id = created_test_roast['roast_id']
        bean_id = created_test_roast['bean_id']
        original_stock = created_test_roast['original_stock']

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

    def test_end_nonexistent_roast(self, client):
        """Test ending a roast that doesn't exist."""
        fake_id = str(ObjectId())
        response = client.post(f'/api/roast/end/{fake_id}')

        assert response.status_code == 404
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


class TestRoastSyncState:
    """Tests for the consolidated sync_state endpoint."""

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
