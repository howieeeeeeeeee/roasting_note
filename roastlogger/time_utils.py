"""Timezone-aware application time helpers."""

from __future__ import annotations

import os
from datetime import datetime

import pytz
from flask import current_app, has_app_context


def get_local_timezone():
    if has_app_context():
        return pytz.timezone(current_app.config["TIMEZONE"])
    return pytz.timezone(os.environ.get("TIMEZONE", "America/New_York"))


def get_current_time_with_tz():
    return datetime.now(get_local_timezone())


def format_date_in_timezone(value, timezone):
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            value = pytz.utc.localize(value)
        return value.astimezone(timezone).strftime("%Y-%m-%d %H:%M")
    return str(value)


def format_seconds(seconds):
    if seconds is None:
        return ""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"
