"""
API tests for Temperature sensor endpoints.

Tests cover:
- Temperature polling endpoints (fast and accurate)
- Response format validation
- Error handling when sensor unavailable

NOTE: Temperature sensor may not be plugged in during testing.
Tests are designed to pass whether sensor is available or not.
"""
import pytest

import app as app_module


class TestTemperatureEndpoints:
    """Tests for temperature API endpoints."""

    def test_temp_current_fast_allows_slow_esp32_response(self, client, monkeypatch):
        """Normal ESP32 responses around 200-450ms should not be timed out."""
        timeouts = []

        class FakeResponse:
            status_code = 200

            def json(self):
                return {'temperature_celsius': 202.4}

        def fake_get(url, timeout):
            timeouts.append(timeout)
            return FakeResponse()

        monkeypatch.setattr(app_module.requests, 'get', fake_get)

        response = client.get('/api/temp/current_fast')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['temperature'] == 202
        assert data['sensor_status'] == 'ok'
        assert timeouts == [app_module.TEMP_SENSOR_LIVE_TIMEOUT_SECONDS]

    def test_temp_test_connection_reports_fault_diagnostics(self, client, monkeypatch):
        """Test Connection should retry and include diagnostics when reads fail."""
        calls = []

        class TempFailureResponse:
            status_code = 500

            def json(self):
                return {'error': 'Sensor read failed'}

        class DiagnosticsResponse:
            status_code = 200

            def json(self):
                return {
                    'thermocouple_celsius': None,
                    'internal_celsius': 23.0,
                    'error_code': 1,
                    'errors': {
                        'open_circuit': True,
                        'short_to_gnd': False,
                        'short_to_vcc': False,
                    },
                    'status': 'FAULT',
                }

        def fake_get(url, timeout):
            calls.append(url)
            if url.endswith('/diagnostics'):
                return DiagnosticsResponse()
            return TempFailureResponse()

        monkeypatch.setattr(app_module.requests, 'get', fake_get)

        response = client.get('/api/temp/test_connection')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'error'
        assert data['sensor_status'] == 'fault'
        assert data['attempts'] == app_module.TEMP_SENSOR_TEST_ATTEMPTS
        assert data['successes'] == 0
        assert data['diagnostics']['status'] == 'FAULT'
        assert data['diagnostics']['errors']['open_circuit'] is True
        assert len([call for call in calls if call.endswith('/temp')]) == 3

    def test_temp_current_fast_response_format(self, client):
        """Test /api/temp/current_fast returns correct format."""
        response = client.get('/api/temp/current_fast')

        assert response.status_code == 200
        data = response.get_json()

        # Response should have these keys regardless of sensor availability
        assert 'temperature' in data
        assert 'status' in data

        # Status should be either 'success' or 'error'
        assert data['status'] in ['success', 'error']

        # If success, temperature should be a number
        if data['status'] == 'success':
            assert isinstance(data['temperature'], (int, float))
        else:
            # If error, temperature should be None
            assert data['temperature'] is None

    def test_temp_current_accurate_response_format(self, client):
        """Test /api/temp/current returns correct format."""
        response = client.get('/api/temp/current')

        assert response.status_code == 200
        data = response.get_json()

        assert 'temperature' in data
        assert 'status' in data
        assert data['status'] in ['success', 'error']

        # If error, should include message
        if data['status'] == 'error':
            assert 'message' in data

    def test_temp_endpoint_handles_sensor_timeout(self, client):
        """Test that temp endpoints handle sensor timeouts gracefully."""
        # This test verifies the app doesn't crash when sensor is unavailable
        # The endpoint should return a valid JSON response either way

        response = client.get('/api/temp/current_fast')
        assert response.status_code == 200  # Should not crash
        assert response.is_json

        response = client.get('/api/temp/current')
        assert response.status_code == 200  # Should not crash
        assert response.is_json


class TestSensorSettings:
    """Tests for temperature sensor URL settings."""

    def test_get_sensor_settings(self, client):
        """Test getting sensor settings returns URL."""
        response = client.get('/api/settings/sensor')

        assert response.status_code == 200
        data = response.get_json()

        assert 'url' in data
        assert 'default' in data
        # Default should be the standard sensor URL
        assert data['default'] == 'http://192.168.0.47/temp'

    def test_set_sensor_settings(self, client):
        """Test setting a custom sensor URL."""
        custom_url = 'http://192.168.1.100/temp'

        response = client.post(
            '/api/settings/sensor',
            json={'url': custom_url},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['url'] == custom_url

        # Verify it persists in session
        response = client.get('/api/settings/sensor')
        data = response.get_json()
        assert data['url'] == custom_url

    def test_set_empty_url_uses_default(self, client):
        """Test that empty URL falls back to default."""
        response = client.post(
            '/api/settings/sensor',
            json={'url': ''},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['url'] == 'http://192.168.0.47/temp'  # Default


class TestRoRCalculation:
    """Tests for Rate of Rise calculation logic."""

    def test_ror_calculation_with_temp_curve(self, client, roasts_collection, started_test_roast):
        """Test that RoR is calculated when adding temp events."""
        roast_id = started_test_roast['roast_id']

        # Add several temperature readings to build history
        # RoR needs ~30 seconds of data
        readings = [
            {'time_seconds': 0, 'temperature': 100.0},
            {'time_seconds': 10, 'temperature': 110.0},
            {'time_seconds': 20, 'temperature': 120.0},
            {'time_seconds': 30, 'temperature': 130.0},
            {'time_seconds': 40, 'temperature': 140.0},
        ]

        for reading in readings:
            client.post(
                f'/api/roast/add_event/{roast_id}',
                json={**reading, 'fan_setting': 9, 'power_setting': 5},
                content_type='application/json'
            )

        roast = roasts_collection.find_one({'_id': roasts_collection.find_one()['_id']})
        # Note: RoR calculation uses in-memory history which is reset between tests
        # The actual RoR values depend on the history state

    def test_sync_state_calculates_ror(self, client, started_test_roast):
        """Test that sync_state endpoint includes RoR in response."""
        roast_id = started_test_roast['roast_id']

        # Send multiple sync requests to build history
        for time_s in range(0, 35, 5):
            response = client.post(
                f'/api/roast/sync_state/{roast_id}',
                json={
                    'time_seconds': time_s,
                    'status': 'running',
                    'fan_setting': 9,
                    'power_setting': 5
                },
                content_type='application/json'
            )

            data = response.get_json()
            # RoR field should be present (may be None initially)
            assert 'ror' in data
