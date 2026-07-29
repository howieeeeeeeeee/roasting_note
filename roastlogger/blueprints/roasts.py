"""Roast lifecycle, event, review, and live-sync routes."""

from __future__ import annotations

import os

from bson.objectid import ObjectId
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    request,
    url_for,
)

from models.roast_helpers import create_draft_roast, update_roast
from roastlogger.database import get_beans_collection, get_roasts_collection
from roastlogger.e2e import document_markers
from roastlogger.routing import register_unprefixed_routes
from roastlogger.services import live_sync, sensor
from roastlogger.services.roast_lifecycle import (
    complete_draft,
    end_roast,
    start_roast,
    update_roast_setup,
)
from roastlogger.time_utils import get_current_time_with_tz


blueprint = Blueprint("roasts", __name__)


def api_roast_create():
    roast_id = create_draft_roast(
        get_roasts_collection(),
        markers=document_markers(),
    )
    return jsonify({"new_roast_id": str(roast_id)})


def api_roast_start(roast_id):
    payload, status = start_roast(roast_id, request.get_json(silent=True) or {})
    return jsonify(payload), status


def api_roast_end(roast_id):
    payload, status = end_roast(roast_id, request.get_json(silent=True) or {})
    return jsonify(payload), status


def api_roast_update_title(roast_id):
    data = request.get_json()
    get_roasts_collection().update_one(
        {"_id": ObjectId(roast_id)},
        {
            "$set": {
                "title": data.get("title", "Untitled Roast"),
                "updated_at": get_current_time_with_tz(),
            }
        },
    )
    return jsonify({"success": True})


def api_roast_update_setup(roast_id):
    payload, status = update_roast_setup(
        roast_id,
        request.get_json(silent=True) or {},
    )
    return jsonify(payload), status


def api_roast_complete_draft(roast_id):
    payload, status = complete_draft(roast_id)
    return jsonify(payload), status


def api_roast_add_timing(roast_id):
    data = request.get_json()
    time_seconds = int(data["time_seconds"])
    maximum = current_app.config["MAX_ROAST_TIME_SECONDS"]
    if time_seconds < 0 or time_seconds > maximum:
        return jsonify(
            {"success": False, "error": f"Invalid time_seconds: {time_seconds}"}
        )

    timing_event = {
        "event_name": data["event_name"],
        "time_seconds": time_seconds,
    }
    temperature = data.get("temperature")
    if temperature is None:
        temperature = sensor.fetch_temperature_from_sensor()
    if temperature is not None:
        timing_event["temperature"] = float(temperature)
    if data.get("fan_setting") is not None:
        timing_event["fan_setting"] = int(data["fan_setting"])
    if data.get("power_setting") is not None:
        timing_event["power_setting"] = int(data["power_setting"])
    if temperature is not None:
        ror = sensor.calculate_ror(roast_id, float(temperature), time_seconds)
        if ror is not None:
            timing_event["ror"] = ror

    get_roasts_collection().update_one(
        {"_id": ObjectId(roast_id)},
        {
            "$push": {"key_timings": timing_event},
            "$set": {"updated_at": get_current_time_with_tz()},
        },
    )
    return jsonify({"success": True})


def api_roast_add_event(roast_id):
    data = request.get_json()
    time_seconds = int(data["time_seconds"])
    maximum = current_app.config["MAX_ROAST_TIME_SECONDS"]
    if time_seconds < 0 or time_seconds > maximum:
        return jsonify(
            {"success": False, "error": f"Invalid time_seconds: {time_seconds}"}
        )

    roast = get_roasts_collection().find_one({"_id": ObjectId(roast_id)})
    fan_setting = data.get("fan_setting")
    power_setting = data.get("power_setting")
    if fan_setting is None or power_setting is None:
        if roast and roast.get("temp_curve"):
            last_event = roast["temp_curve"][-1]
            if fan_setting is None:
                fan_setting = last_event.get("fan_setting", 9)
            if power_setting is None:
                power_setting = last_event.get("power_setting", 3)
        else:
            fan_setting = 9 if fan_setting is None else fan_setting
            power_setting = 3 if power_setting is None else power_setting
        fan_setting = 9 if fan_setting is None else fan_setting
        power_setting = 3 if power_setting is None else power_setting

    temp_event = {
        "time_seconds": time_seconds,
        "fan_setting": int(fan_setting),
        "power_setting": int(power_setting),
    }
    if data.get("temperature") is not None:
        temp_event["temperature"] = float(data["temperature"])
    if data.get("ror") is not None:
        temp_event["ror"] = float(data["ror"])
    elif data.get("temperature") is not None:
        ror = sensor.calculate_ror(
            roast_id,
            float(data["temperature"]),
            time_seconds,
        )
        if ror is not None:
            temp_event["ror"] = ror
    if data.get("note"):
        temp_event["note"] = data["note"]

    get_roasts_collection().update_one(
        {"_id": ObjectId(roast_id)},
        {
            "$push": {"temp_curve": temp_event},
            "$set": {"updated_at": get_current_time_with_tz()},
        },
    )
    return jsonify({"success": True})


def api_roast_log_temp_local(roast_id):
    data = request.get_json()
    logs_dir = current_app.config["TEMP_LOG_DIR"]
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"{roast_id}.csv")
    file_exists = os.path.exists(log_file)
    with open(log_file, "a") as handle:
        if not file_exists:
            handle.write("time_seconds,temperature,ror\n")
        ror = data.get("ror")
        ror_value = f"{ror}" if ror is not None else ""
        handle.write(
            f"{data.get('time_seconds')},{data.get('temperature')},{ror_value}\n"
        )
    return jsonify({"success": True})


def api_roast_update(roast_id):
    update_roast(
        get_roasts_collection(),
        get_beans_collection(),
        roast_id,
        request.form.to_dict(),
    )
    return redirect(url_for("roast_detail", roast_id=roast_id))


def api_roast_delete(roast_id):
    roast = get_roasts_collection().find_one({"_id": ObjectId(roast_id)})
    current_time = get_current_time_with_tz()
    if (
        roast
        and roast.get("roast_start_time")
        and roast.get("bean_id")
        and roast.get("original_weight_grams")
    ):
        get_beans_collection().update_one(
            {"_id": ObjectId(roast["bean_id"])},
            {
                "$inc": {"stock_grams": roast["original_weight_grams"]},
                "$set": {"updated_at": current_time},
            },
        )
    get_roasts_collection().update_one(
        {"_id": ObjectId(roast_id)},
        {"$set": {"archived": True, "updated_at": current_time}},
    )
    return redirect(url_for("index"))


def api_roast_add_review(roast_id):
    data = request.get_json(silent=True) or request.form.to_dict()
    current_time = get_current_time_with_tz()
    review = {
        "_id": ObjectId(),
        "overall_score": int(data.get("overall_score", 3)),
        "extraction_method": data.get("extraction_method", ""),
        "notes": data.get("notes", ""),
        "review_date": current_time,
        "created_at": current_time,
        "updated_at": current_time,
    }
    get_roasts_collection().update_one(
        {"_id": ObjectId(roast_id)},
        {"$push": {"reviews": review}, "$set": {"updated_at": current_time}},
    )
    if request.is_json:
        return jsonify({"success": True, "review_id": str(review["_id"])})
    return redirect(url_for("roast_detail", roast_id=roast_id))


def api_roast_update_review(roast_id, review_id):
    data = request.get_json(silent=True) or request.form.to_dict()
    current_time = get_current_time_with_tz()
    get_roasts_collection().update_one(
        {"_id": ObjectId(roast_id), "reviews._id": ObjectId(review_id)},
        {
            "$set": {
                "reviews.$.overall_score": int(data.get("overall_score", 3)),
                "reviews.$.extraction_method": data.get(
                    "extraction_method",
                    "",
                ),
                "reviews.$.notes": data.get("notes", ""),
                "reviews.$.updated_at": current_time,
                "updated_at": current_time,
            }
        },
    )
    if request.is_json:
        return jsonify({"success": True})
    return redirect(url_for("roast_detail", roast_id=roast_id))


def api_roast_delete_review(roast_id, review_id):
    get_roasts_collection().update_one(
        {"_id": ObjectId(roast_id)},
        {
            "$pull": {"reviews": {"_id": ObjectId(review_id)}},
            "$set": {"updated_at": get_current_time_with_tz()},
        },
    )
    if request.is_json:
        return jsonify({"success": True})
    return redirect(url_for("roast_detail", roast_id=roast_id))


def api_roast_sync_state(roast_id):
    data = request.get_json()
    compatibility = current_app.extensions.get("roastlogger_compat")
    reading_provider = (
        getattr(compatibility, "fetch_temperature_reading", None)
        if compatibility
        else None
    )
    response = live_sync.sync_roast_state(
        roast_id,
        int(data.get("time_seconds", 0)),
        data.get("status", "stopped"),
        int(data.get("fan_setting", 0)),
        int(data.get("power_setting", 0)),
        reading_provider=reading_provider,
    )
    return jsonify(response)


register_unprefixed_routes(
    blueprint,
    [
        ("/api/roast/create", "api_roast_create", api_roast_create, ["POST"]),
        (
            "/api/roast/start/<roast_id>",
            "api_roast_start",
            api_roast_start,
            ["POST"],
        ),
        (
            "/api/roast/end/<roast_id>",
            "api_roast_end",
            api_roast_end,
            ["POST"],
        ),
        (
            "/api/roast/update_title/<roast_id>",
            "api_roast_update_title",
            api_roast_update_title,
            ["POST"],
        ),
        (
            "/api/roast/update_setup/<roast_id>",
            "api_roast_update_setup",
            api_roast_update_setup,
            ["POST"],
        ),
        (
            "/api/roast/complete_draft/<roast_id>",
            "api_roast_complete_draft",
            api_roast_complete_draft,
            ["POST"],
        ),
        (
            "/api/roast/add_timing/<roast_id>",
            "api_roast_add_timing",
            api_roast_add_timing,
            ["POST"],
        ),
        (
            "/api/roast/add_event/<roast_id>",
            "api_roast_add_event",
            api_roast_add_event,
            ["POST"],
        ),
        (
            "/api/roast/log_temp_local/<roast_id>",
            "api_roast_log_temp_local",
            api_roast_log_temp_local,
            ["POST"],
        ),
        (
            "/api/roast/update/<roast_id>",
            "api_roast_update",
            api_roast_update,
            ["POST"],
        ),
        (
            "/api/roast/delete/<roast_id>",
            "api_roast_delete",
            api_roast_delete,
            ["POST"],
        ),
        (
            "/api/roast/add_review/<roast_id>",
            "api_roast_add_review",
            api_roast_add_review,
            ["POST"],
        ),
        (
            "/api/roast/update_review/<roast_id>/<review_id>",
            "api_roast_update_review",
            api_roast_update_review,
            ["POST"],
        ),
        (
            "/api/roast/delete_review/<roast_id>/<review_id>",
            "api_roast_delete_review",
            api_roast_delete_review,
            ["POST"],
        ),
        (
            "/api/roast/sync_state/<roast_id>",
            "api_roast_sync_state",
            api_roast_sync_state,
            ["POST"],
        ),
    ],
)
