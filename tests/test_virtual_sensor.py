"""Virtual-sensor scenario and RoastLogger integration contracts."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager

import requests
from werkzeug.serving import make_server

from roastlogger import create_app
from roastlogger.e2e import E2E_DATABASE_NAME
from tests.e2e.virtual_sensor import SCENARIOS, create_sensor_app


def set_scenario(client, scenario, **values):
    return client.post(
        "/__e2e/scenario",
        json={"scenario": scenario, **values},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    )


def test_virtual_sensor_exposes_every_deterministic_scenario():
    app = create_sensor_app(slow_delay=0.001, timeout_delay=0.01)
    client = app.test_client()

    assert SCENARIOS == {
        "healthy-ramp",
        "slow-success",
        "rate-limited",
        "timeout",
        "offline",
        "malformed",
        "fault",
    }
    healthy_one = client.get("/temp").json["temperature_celsius"]
    healthy_two = client.get("/temp").json["temperature_celsius"]
    assert healthy_two > healthy_one

    set_scenario(client, "slow-success")
    started = time.monotonic()
    assert client.get("/temp").status_code == 200
    assert time.monotonic() - started >= 0.001

    set_scenario(client, "rate-limited", rate_limit_calls=2)
    assert client.get("/temp").status_code == 429
    assert client.get("/temp").status_code == 429
    assert client.get("/temp").status_code == 200

    set_scenario(client, "timeout")
    started = time.monotonic()
    assert client.get("/temp").status_code == 200
    assert time.monotonic() - started >= 0.01

    set_scenario(client, "offline")
    assert client.get("/temp").status_code == 503

    set_scenario(client, "malformed")
    malformed = client.get("/temp")
    assert malformed.status_code == 200
    assert malformed.get_json(silent=True) is None

    set_scenario(client, "fault")
    assert client.get("/temp").status_code == 503
    diagnostics = client.get("/diagnostics").json
    assert diagnostics["status"] == "FAULT"
    assert diagnostics["error_code"] == 5
    assert diagnostics["errors"] == ["open_circuit", "short_to_ground"]


def test_virtual_sensor_control_is_loopback_only():
    client = create_sensor_app().test_client()
    response = client.post(
        "/__e2e/scenario",
        json={"scenario": "healthy-ramp"},
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )
    assert response.status_code == 403


@contextmanager
def running_sensor():
    sensor_app = create_sensor_app(
        slow_delay=0.01,
        timeout_delay=0.2,
    )
    server = make_server(
        "127.0.0.1",
        0,
        sensor_app,
        threaded=True,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_roastlogger_recovers_after_rate_limit_and_reports_fault(tmp_path):
    with running_sensor() as sensor_base:
        app = create_app(
            {
                "TESTING": True,
                "DEVICE": "sensor-integration",
                "E2E_MODE": True,
                "E2E_RUN_ID": "sensor-integration",
                "E2E_ARTIFACT_ROOT": str(tmp_path),
                "LOCAL_DB_NAME": E2E_DATABASE_NAME,
                "MONGO_URI_LOCAL": "mongodb://127.0.0.1:27017/",
                "TEMP_SENSOR_URL": f"{sensor_base}/temp",
                "TEMP_SENSOR_LIVE_ATTEMPTS": 3,
                "TEMP_SENSOR_TEST_ATTEMPTS": 2,
                "TEMP_SENSOR_LIVE_TIMEOUT_SECONDS": 0.1,
            }
        )
        client = app.test_client()
        requests.post(
            f"{sensor_base}/__e2e/scenario",
            json={"scenario": "rate-limited", "rate_limit_calls": 1},
            timeout=1,
        ).raise_for_status()

        retrying = client.get("/api/temp/current").json
        assert retrying["status"] == "success"
        assert retrying["sensor_status"] == "retrying"
        assert retrying["successes"] == 2

        requests.post(
            f"{sensor_base}/__e2e/scenario",
            json={"scenario": "fault"},
            timeout=1,
        ).raise_for_status()
        fault = client.get("/api/temp/test_connection").json
        assert fault["status"] == "error"
        assert fault["sensor_status"] == "fault"
        assert fault["diagnostics"]["error_code"] == 5

        requests.post(
            f"{sensor_base}/__e2e/scenario",
            json={"scenario": "healthy-ramp"},
            timeout=1,
        ).raise_for_status()
        recovered = client.get("/api/temp/current_fast").json
        assert recovered["status"] == "success"
        assert recovered["sensor_status"] == "ok"
        app.extensions["roastlogger_databases"].local_client.close()
