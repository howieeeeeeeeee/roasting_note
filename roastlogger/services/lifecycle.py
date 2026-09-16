"""Roast lifecycle state and display behavior."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import url_for

from roastlogger.config import (
    ROAST_LIFECYCLE_COMPLETED,
    ROAST_LIFECYCLE_DRAFT,
    ROAST_LIFECYCLE_STARTED,
    VALID_ROAST_LIFECYCLE_STATUSES,
)


def get_roast_lifecycle_status(roast):
    lifecycle_status = roast.get("lifecycle_status")
    if lifecycle_status in VALID_ROAST_LIFECYCLE_STATUSES:
        return lifecycle_status
    if roast.get("roast_end_time"):
        return ROAST_LIFECYCLE_COMPLETED
    if roast.get("roast_start_time"):
        return ROAST_LIFECYCLE_STARTED
    return ROAST_LIFECYCLE_DRAFT


def annotate_roast_lifecycle(roast):
    lifecycle_status = get_roast_lifecycle_status(roast)
    roast["lifecycle_state"] = lifecycle_status

    if lifecycle_status == ROAST_LIFECYCLE_COMPLETED:
        roast["lifecycle_label"] = "Completed"
        roast["lifecycle_action_label"] = "View"
        roast["lifecycle_icon"] = "visibility"
        roast["lifecycle_url"] = url_for("roast_detail", roast_id=roast["_id"])
    elif lifecycle_status == ROAST_LIFECYCLE_STARTED:
        roast["lifecycle_label"] = "In Progress"
        roast["lifecycle_action_label"] = "Resume Roast"
        roast["lifecycle_icon"] = "play_circle"
        roast["lifecycle_url"] = url_for("roast_live", roast_id=roast["_id"])
    else:
        roast["lifecycle_label"] = "Draft"
        roast["lifecycle_action_label"] = "Resume Setup"
        roast["lifecycle_icon"] = "edit_note"
        roast["lifecycle_url"] = url_for("roast_live", roast_id=roast["_id"])

    return roast


def latest_roast_dates(roasts):
    """Latest completed, non-archived roast per bean, without storing summaries."""
    dates = {}
    for roast in roasts:
        if roast.get("archived") or get_roast_lifecycle_status(roast) != ROAST_LIFECYCLE_COMPLETED:
            continue
        bean_id = roast.get("bean_id")
        date = roast.get("roast_start_time") or roast.get("roast_date")
        if bean_id is None or not isinstance(date, datetime):
            continue
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        if bean_id not in dates or date > dates[bean_id]:
            dates[bean_id] = date
    return dates
