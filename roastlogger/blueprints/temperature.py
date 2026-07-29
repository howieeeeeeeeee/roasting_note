"""Temperature sensor API routes."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from roastlogger.routing import register_unprefixed_routes
from roastlogger.services import sensor


blueprint = Blueprint("temperature", __name__)


def api_temp_current_fast():
    reading = sensor.fetch_temperature_reading(attempts=1)
    return jsonify(sensor.build_temperature_response(reading))


def api_temp_test_connection():
    reading = sensor.fetch_temperature_reading(
        attempts=current_app.config["TEMP_SENSOR_TEST_ATTEMPTS"],
        min_successes=1,
        include_diagnostics=True,
    )
    response = sensor.build_temperature_response(reading)
    if reading["temperature"] is not None:
        if reading["sensor_status"] == "retrying":
            response["message"] = (
                f"Connected after retry. Current temp: {reading['temperature']}°C"
            )
        else:
            response["message"] = f"Connected. Current temp: {reading['temperature']}°C"
    elif reading["sensor_status"] == "fault":
        response["message"] = "Sensor hardware reported a fault"
    else:
        response["message"] = "Sensor unavailable after retry"
    return jsonify(response)


def api_temp_current():
    reading = sensor.fetch_temperature_reading(
        attempts=current_app.config["TEMP_SENSOR_LIVE_ATTEMPTS"],
        min_successes=2,
        include_diagnostics=True,
    )
    response = sensor.build_temperature_response(reading)
    if reading["temperature"] is None and "message" not in response:
        response["message"] = "Insufficient readings or sensor unavailable"
    return jsonify(response)


register_unprefixed_routes(
    blueprint,
    [
        (
            "/api/temp/current_fast",
            "api_temp_current_fast",
            api_temp_current_fast,
            ["GET"],
        ),
        (
            "/api/temp/test_connection",
            "api_temp_test_connection",
            api_temp_test_connection,
            ["GET"],
        ),
        (
            "/api/temp/current",
            "api_temp_current",
            api_temp_current,
            ["GET"],
        ),
    ],
)
