"""Stable development and Gunicorn entry point for RoastLogger."""

from __future__ import annotations

import sys
from datetime import datetime

import pytz
import requests
from bson.objectid import ObjectId

from roastlogger import create_app
from roastlogger.config import (
    DB_LOG_INTERVAL_SECONDS,
    DEFAULT_TEMP_SENSOR_URL,
    MAX_ROAST_TIME_SECONDS,
    MAX_SENSOR_DIAGNOSTICS,
    ROAST_LIFECYCLE_COMPLETED,
    ROAST_LIFECYCLE_DRAFT,
    ROAST_LIFECYCLE_STARTED,
    ROR_TOLERANCE_SECONDS,
    ROR_WINDOW_SECONDS,
    TEMP_SENSOR_LIVE_ATTEMPTS,
    TEMP_SENSOR_LIVE_TIMEOUT_SECONDS,
    TEMP_SENSOR_STALE_SECONDS,
    TEMP_SENSOR_TEST_ATTEMPTS,
    VALID_ROAST_LIFECYCLE_STATUSES,
)
from roastlogger.database import (
    get_beans_collection,
    get_connections,
    get_current_db_mode,
    get_roasts_collection,
)
from roastlogger.services.database_sync import (
    normalize_sync_timestamp,
    prepare_synced_document,
    sync_collection,
)
from roastlogger.services.lifecycle import (
    annotate_roast_lifecycle,
    get_roast_lifecycle_status,
)
from roastlogger.services.sensor import (
    build_sensor_diagnostic_event,
    build_temperature_response,
    calculate_ror,
    compact_sensor_diagnostics,
    derive_live_sensor_status,
    fetch_sensor_diagnostics,
    fetch_temperature_from_sensor,
    fetch_temperature_from_sensor_fast,
    fetch_temperature_reading,
    get_temp_diagnostics_url,
    get_temp_sensor_url,
    log_sensor_diagnostics_csv,
    roast_temp_history,
)


app = create_app()
app.extensions["roastlogger_compat"] = sys.modules[__name__]

_connections = app.extensions["roastlogger_databases"]
mongo_online = _connections.online_client
mongo_local = _connections.local_client
db_online = _connections.online_db
db_local = _connections.local_db

DEFAULT_DB = app.config["DEFAULT_DB"]
MONGO_URI_ONLINE = app.config["MONGO_URI"]
MONGO_URI_LOCAL = app.config["MONGO_URI_LOCAL"]
TIMEZONE = app.config["TIMEZONE"]
local_tz = pytz.timezone(TIMEZONE)


def get_current_time_with_tz():
    return datetime.now(local_tz)


def append_roast_sensor_diagnostic(roast_id, diagnostic_event):
    try:
        get_roasts_collection().update_one(
            {"_id": ObjectId(roast_id)},
            {
                "$push": {
                    "sensor_diagnostics": {
                        "$each": [diagnostic_event],
                        "$slice": -MAX_SENSOR_DIAGNOSTICS,
                    }
                },
                "$set": {"updated_at": get_current_time_with_tz()},
            },
        )
    except Exception as exc:
        print(f"Error logging sensor diagnostic to MongoDB: {exc}")


def format_date(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            value = pytz.utc.localize(value)
        return value.astimezone(local_tz).strftime("%Y-%m-%d %H:%M")
    return str(value)


def format_seconds(seconds):
    if seconds is None:
        return ""
    minutes = int(seconds // 60)
    remainder = int(seconds % 60)
    return f"{minutes:02d}:{remainder:02d}"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
