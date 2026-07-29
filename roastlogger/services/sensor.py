"""Temperature sensor access and Rate of Rise calculation."""

from __future__ import annotations

import collections
import os
import time
from urllib.parse import urlsplit, urlunsplit

import requests
from bson.objectid import ObjectId
from flask import current_app, session

from roastlogger.database import get_roasts_collection
from roastlogger.time_utils import get_current_time_with_tz


roast_temp_history = {}


def get_temp_sensor_url():
    return session.get("temp_sensor_url", current_app.config["TEMP_SENSOR_URL"])


def get_temp_diagnostics_url(sensor_url=None):
    parsed = urlsplit(sensor_url or get_temp_sensor_url())
    path = parsed.path or "/"
    if path.rstrip("/").endswith("/temp"):
        diagnostics_path = path.rstrip("/")[: -len("/temp")] + "/diagnostics"
    elif path.endswith("/"):
        diagnostics_path = f"{path}diagnostics"
    else:
        diagnostics_path = f"{path.rstrip('/')}/diagnostics"
    return urlunsplit((parsed.scheme, parsed.netloc, diagnostics_path, "", ""))


def compact_sensor_diagnostics(diagnostics):
    if not diagnostics:
        return None
    return {
        "status": diagnostics.get("status"),
        "error_code": diagnostics.get("error_code"),
        "errors": diagnostics.get("errors"),
        "thermocouple_celsius": diagnostics.get("thermocouple_celsius"),
        "internal_celsius": diagnostics.get("internal_celsius"),
    }


def fetch_sensor_diagnostics(sensor_url=None, timeout=None):
    timeout = timeout or current_app.config["TEMP_SENSOR_LIVE_TIMEOUT_SECONDS"]
    diagnostics_url = get_temp_diagnostics_url(sensor_url)
    started_at = time.monotonic()
    try:
        response = requests.get(diagnostics_url, timeout=timeout)
        duration_ms = round((time.monotonic() - started_at) * 1000)
        if response.status_code != 200:
            return {
                "available": False,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "error": f"http_{response.status_code}",
            }
        data = response.json()
        compact = compact_sensor_diagnostics(data) or {}
        compact.update({"available": True, "duration_ms": duration_ms})
        return compact
    except requests.exceptions.Timeout:
        return {"available": False, "error": "timeout"}
    except requests.exceptions.RequestException as exc:
        return {"available": False, "error": exc.__class__.__name__}
    except (ValueError, KeyError):
        return {"available": False, "error": "invalid_json"}


def fetch_temperature_reading(
    attempts=None,
    timeout=None,
    min_successes=1,
    include_diagnostics=False,
):
    attempts = attempts or current_app.config["TEMP_SENSOR_LIVE_ATTEMPTS"]
    timeout = timeout or current_app.config["TEMP_SENSOR_LIVE_TIMEOUT_SECONDS"]
    sensor_url = get_temp_sensor_url()
    started_at = time.monotonic()
    readings = []
    attempt_results = []
    first_success_attempt = None

    for attempt_number in range(1, attempts + 1):
        attempt_started_at = time.monotonic()
        result = {
            "attempt": attempt_number,
            "success": False,
            "duration_ms": None,
            "error": None,
        }
        try:
            response = requests.get(sensor_url, timeout=timeout)
            result["duration_ms"] = round(
                (time.monotonic() - attempt_started_at) * 1000
            )
            if response.status_code != 200:
                result["error"] = f"http_{response.status_code}"
            else:
                data = response.json()
                temperature = data.get("temperature_celsius") or data.get(
                    "temperatur_celsius"
                )
                if temperature is None:
                    result["error"] = "missing_temperature"
                else:
                    readings.append(float(temperature))
                    result["success"] = True
                    if first_success_attempt is None:
                        first_success_attempt = attempt_number
        except requests.exceptions.Timeout:
            result["duration_ms"] = round(
                (time.monotonic() - attempt_started_at) * 1000
            )
            result["error"] = "timeout"
        except requests.exceptions.RequestException as exc:
            result["duration_ms"] = round(
                (time.monotonic() - attempt_started_at) * 1000
            )
            result["error"] = exc.__class__.__name__
        except (ValueError, KeyError):
            result["duration_ms"] = round(
                (time.monotonic() - attempt_started_at) * 1000
            )
            result["error"] = "invalid_json"
        attempt_results.append(result)

    successes = len(readings)
    temperature = None
    sensor_status = "offline"
    if successes >= min_successes:
        top_readings = sorted(readings, reverse=True)[:2]
        temperature = round(sum(top_readings) / len(top_readings))
        sensor_status = "ok" if first_success_attempt == 1 else "retrying"
    elif successes > 0:
        sensor_status = "retrying"

    errors = [
        attempt["error"]
        for attempt in attempt_results
        if not attempt["success"] and attempt["error"]
    ]
    diagnostics = None
    if temperature is None and include_diagnostics:
        diagnostics = fetch_sensor_diagnostics(sensor_url=sensor_url, timeout=timeout)
        if (
            diagnostics.get("available")
            and diagnostics.get("status")
            and diagnostics.get("status") != "OK"
        ):
            sensor_status = "fault"

    return {
        "temperature": temperature,
        "sensor_status": sensor_status,
        "attempts": attempts,
        "successes": successes,
        "duration_ms": round((time.monotonic() - started_at) * 1000),
        "errors": errors,
        "attempt_results": attempt_results,
        "diagnostics": diagnostics,
    }


def build_temperature_response(reading, status_key="status"):
    response = {
        "temperature": reading["temperature"],
        status_key: "success" if reading["temperature"] is not None else "error",
        "sensor_status": reading["sensor_status"],
        "attempts": reading["attempts"],
        "successes": reading["successes"],
        "duration_ms": reading["duration_ms"],
    }
    if reading.get("errors"):
        response["errors"] = reading["errors"]
        response["message"] = ", ".join(reading["errors"])
    if reading.get("diagnostics"):
        response["diagnostics"] = reading["diagnostics"]
    return response


def fetch_temperature_from_sensor_fast():
    return fetch_temperature_reading(attempts=1)["temperature"]


def fetch_temperature_from_sensor():
    return fetch_temperature_reading(min_successes=2)["temperature"]


def calculate_ror(roast_id, current_temp, current_time):
    if roast_id not in roast_temp_history:
        roast_temp_history[roast_id] = {
            "history": collections.deque(maxlen=60),
            "last_db_log_time": -1,
        }
    history = roast_temp_history[roast_id]["history"]
    history.append({"time": current_time, "temp": current_temp})
    window = current_app.config["ROR_WINDOW_SECONDS"]
    if current_time < window:
        return None

    target_time = current_time - window
    tolerance = current_app.config["ROR_TOLERANCE_SECONDS"]
    best_reading = None
    best_diff = float("inf")
    for reading in history:
        difference = abs(reading["time"] - target_time)
        if difference <= tolerance and difference < best_diff:
            best_reading = reading
            best_diff = difference
    if best_reading:
        time_difference = current_time - best_reading["time"]
        if time_difference > 0:
            return round(
                ((current_temp - best_reading["temp"]) / time_difference) * 60,
                1,
            )
    return None


def derive_live_sensor_status(reading, last_success_age_seconds):
    if reading["temperature"] is not None:
        return reading["sensor_status"]
    if reading["sensor_status"] == "fault":
        return "fault"
    if last_success_age_seconds is None:
        return "offline"
    if last_success_age_seconds >= current_app.config["TEMP_SENSOR_STALE_SECONDS"]:
        return "stale"
    return "retrying"


def build_sensor_diagnostic_event(
    client_time,
    reading,
    sensor_status,
    last_success_age,
):
    event = {
        "time_seconds": client_time,
        "sensor_status": sensor_status,
        "temperature": reading["temperature"],
        "attempts": reading["attempts"],
        "successes": reading["successes"],
        "duration_ms": reading["duration_ms"],
        "last_success_age_seconds": last_success_age,
        "created_at": get_current_time_with_tz(),
    }
    if reading.get("errors"):
        event["errors"] = reading["errors"]
    if reading.get("diagnostics"):
        event["diagnostics"] = reading["diagnostics"]
    return event


def log_sensor_diagnostics_csv(roast_id, diagnostic_event):
    try:
        logs_dir = os.path.join(os.getcwd(), "temp_logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, f"{roast_id}_sensor_diagnostics.csv")
        file_exists = os.path.exists(log_file)
        with open(log_file, "a") as handle:
            if not file_exists:
                handle.write(
                    "time_seconds,sensor_status,temperature,attempts,successes,"
                    "duration_ms,last_success_age_seconds,errors\n"
                )
            errors = "|".join(diagnostic_event.get("errors", []))
            temperature = diagnostic_event.get("temperature")
            last_success_age = diagnostic_event.get("last_success_age_seconds")
            handle.write(
                f"{diagnostic_event['time_seconds']},"
                f"{diagnostic_event['sensor_status']},"
                f"{temperature if temperature is not None else ''},"
                f"{diagnostic_event['attempts']},"
                f"{diagnostic_event['successes']},"
                f"{diagnostic_event['duration_ms']},"
                f"{last_success_age if last_success_age is not None else ''},"
                f"{errors}\n"
            )
    except Exception as exc:
        print(f"Error logging sensor diagnostics CSV: {exc}")


def append_roast_sensor_diagnostic(roast_id, diagnostic_event, collection=None):
    try:
        (collection or get_roasts_collection()).update_one(
            {"_id": ObjectId(roast_id)},
            {
                "$push": {
                    "sensor_diagnostics": {
                        "$each": [diagnostic_event],
                        "$slice": -current_app.config["MAX_SENSOR_DIAGNOSTICS"],
                    }
                },
                "$set": {"updated_at": get_current_time_with_tz()},
            },
        )
    except Exception as exc:
        print(f"Error logging sensor diagnostic to MongoDB: {exc}")
