"""Application configuration defaults."""

from __future__ import annotations

import os


DEFAULT_TEMP_SENSOR_URL = "http://192.168.0.47/temp"
ROAST_LIFECYCLE_DRAFT = "draft"
ROAST_LIFECYCLE_STARTED = "started"
ROAST_LIFECYCLE_COMPLETED = "completed"
VALID_ROAST_LIFECYCLE_STATUSES = {
    ROAST_LIFECYCLE_DRAFT,
    ROAST_LIFECYCLE_STARTED,
    ROAST_LIFECYCLE_COMPLETED,
}

ROR_WINDOW_SECONDS = 20
ROR_TOLERANCE_SECONDS = 5
DB_LOG_INTERVAL_SECONDS = 1
MAX_ROAST_TIME_SECONDS = 7200
TEMP_SENSOR_LIVE_ATTEMPTS = 3
TEMP_SENSOR_LIVE_TIMEOUT_SECONDS = 0.75
TEMP_SENSOR_TEST_ATTEMPTS = 3
TEMP_SENSOR_STALE_SECONDS = 5
MAX_SENSOR_DIAGNOSTICS = 300


def _default_db_mode() -> str:
    mode = os.environ.get("DEFAULT_DB", "local").strip().lower() or "local"
    return mode if mode in {"local", "online"} else "local"


def default_config() -> dict[str, object]:
    return {
        "SECRET_KEY": os.environ.get(
            "SECRET_KEY",
            "dev-secret-key-change-in-production",
        ),
        "DEFAULT_DB": _default_db_mode(),
        "DEVICE": os.environ.get("DEVICE", ""),
        "LOCAL_DB_NAME": os.environ.get("LOCAL_DB_NAME", "roastlogger"),
        "ONLINE_DB_NAME": "roastlogger",
        "MONGO_URI": os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
        "MONGO_URI_LOCAL": os.environ.get(
            "MONGO_URI_LOCAL",
            "mongodb://localhost:27017/",
        ),
        "TEMP_SENSOR_URL": os.environ.get(
            "TEMP_SENSOR_URL",
            DEFAULT_TEMP_SENSOR_URL,
        ),
        "TIMEZONE": os.environ.get("TIMEZONE", "America/New_York"),
        "ROR_WINDOW_SECONDS": ROR_WINDOW_SECONDS,
        "ROR_TOLERANCE_SECONDS": ROR_TOLERANCE_SECONDS,
        "DB_LOG_INTERVAL_SECONDS": DB_LOG_INTERVAL_SECONDS,
        "MAX_ROAST_TIME_SECONDS": MAX_ROAST_TIME_SECONDS,
        "TEMP_SENSOR_LIVE_ATTEMPTS": TEMP_SENSOR_LIVE_ATTEMPTS,
        "TEMP_SENSOR_LIVE_TIMEOUT_SECONDS": TEMP_SENSOR_LIVE_TIMEOUT_SECONDS,
        "TEMP_SENSOR_TEST_ATTEMPTS": TEMP_SENSOR_TEST_ATTEMPTS,
        "TEMP_SENSOR_STALE_SECONDS": TEMP_SENSOR_STALE_SECONDS,
        "MAX_SENSOR_DIAGNOSTICS": MAX_SENSOR_DIAGNOSTICS,
    }
