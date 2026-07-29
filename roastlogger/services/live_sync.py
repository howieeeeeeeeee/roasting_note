"""Live-roast polling, local logging, and MongoDB logging."""

from __future__ import annotations

import collections
import os

from bson.objectid import ObjectId
from flask import current_app

from roastlogger.database import get_roasts_collection
from roastlogger.services import sensor
from roastlogger.time_utils import get_current_time_with_tz


def _state_for(roast_id):
    if roast_id not in sensor.roast_temp_history:
        sensor.roast_temp_history[roast_id] = {
            "history": collections.deque(maxlen=60),
            "last_db_log_time": -1,
            "last_fan": -1,
            "last_power": -1,
            "last_success_time_seconds": None,
        }
    return sensor.roast_temp_history[roast_id]


def _log_temperature_csv(roast_id, client_time, temperature, ror):
    logs_dir = os.path.join(os.getcwd(), "temp_logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"{roast_id}.csv")
    file_exists = os.path.exists(log_file)
    with open(log_file, "a") as handle:
        if not file_exists:
            handle.write("time_seconds,temperature,ror\n")
        ror_value = str(ror) if ror is not None else ""
        handle.write(f"{client_time},{temperature},{ror_value}\n")


def sync_roast_state(
    roast_id,
    client_time,
    status,
    fan_setting,
    power_setting,
    reading_provider=None,
):
    maximum = current_app.config["MAX_ROAST_TIME_SECONDS"]
    if client_time < 0 or client_time > maximum:
        return {
            "success": False,
            "error": (
                f"Invalid time_seconds: {client_time}. "
                f"Must be between 0 and {maximum}."
            ),
            "temperature": None,
            "ror": None,
            "logged_to_db": False,
            "sensor_status": "offline",
        }

    state = _state_for(roast_id)
    settings_changed = (fan_setting != state.get("last_fan", -1)) or (
        power_setting != state.get("last_power", -1)
    )
    interval = current_app.config["DB_LOG_INTERVAL_SECONDS"]
    current_interval = client_time // interval
    last_interval = state["last_db_log_time"] // interval
    is_db_log_interval = (
        (current_interval > last_interval) and client_time > 0
    ) or settings_changed

    if settings_changed:
        state["last_fan"] = fan_setting
        state["last_power"] = power_setting

    fetch = reading_provider or sensor.fetch_temperature_reading
    reading = fetch(
        attempts=current_app.config["TEMP_SENSOR_LIVE_ATTEMPTS"],
        min_successes=1,
        include_diagnostics=True,
    )
    temperature = reading["temperature"]
    if temperature is not None:
        state["last_success_time_seconds"] = client_time
        last_success_age = 0
    elif state.get("last_success_time_seconds") is not None:
        last_success_age = max(
            0,
            client_time - state["last_success_time_seconds"],
        )
    else:
        last_success_age = None

    sensor_status = sensor.derive_live_sensor_status(reading, last_success_age)
    diagnostic_event = sensor.build_sensor_diagnostic_event(
        client_time,
        reading,
        sensor_status,
        last_success_age,
    )
    if status == "running":
        sensor.log_sensor_diagnostics_csv(roast_id, diagnostic_event)
        if sensor_status != "ok":
            sensor.append_roast_sensor_diagnostic(roast_id, diagnostic_event)

    response = {
        "success": True,
        "temperature": temperature,
        "ror": None,
        "logged_to_db": False,
        "sensor_status": sensor_status,
        "attempts": reading["attempts"],
        "successes": reading["successes"],
        "duration_ms": reading["duration_ms"],
        "last_success_age_seconds": last_success_age,
    }
    if reading.get("errors"):
        response["errors"] = reading["errors"]
    if reading.get("diagnostics"):
        response["diagnostics"] = reading["diagnostics"]
    if temperature is None:
        return response

    ror = sensor.calculate_ror(roast_id, temperature, client_time)
    response["ror"] = ror
    if status != "running":
        return response

    try:
        _log_temperature_csv(roast_id, client_time, temperature, ror)
    except Exception as exc:
        print(f"Error logging local CSV: {exc}")

    if is_db_log_interval:
        try:
            temp_event = {
                "time_seconds": client_time,
                "temperature": float(temperature),
                "fan_setting": fan_setting,
                "power_setting": power_setting,
                "ror": ror,
                "sensor_status": sensor_status,
                "sensor_attempts": reading["attempts"],
                "sensor_successes": reading["successes"],
                "sensor_read_ms": reading["duration_ms"],
            }
            get_roasts_collection().update_one(
                {"_id": ObjectId(roast_id)},
                {
                    "$push": {"temp_curve": temp_event},
                    "$set": {"updated_at": get_current_time_with_tz()},
                },
            )
            response["logged_to_db"] = True
            state["last_db_log_time"] = client_time
        except Exception as exc:
            print(f"Error logging to MongoDB: {exc}")
    return response
