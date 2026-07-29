"""Roast lifecycle mutations independent of Flask request handling."""

from __future__ import annotations

from bson.objectid import ObjectId
from flask import current_app

from roastlogger.config import (
    ROAST_LIFECYCLE_COMPLETED,
    ROAST_LIFECYCLE_DRAFT,
    ROAST_LIFECYCLE_STARTED,
)
from roastlogger.database import get_beans_collection, get_roasts_collection
from roastlogger.services.lifecycle import get_roast_lifecycle_status
from roastlogger.services.sensor import fetch_temperature_from_sensor
from roastlogger.time_utils import get_current_time_with_tz, get_local_timezone


def start_roast(roast_id, data):
    roasts = get_roasts_collection()
    roast = roasts.find_one(
        {"_id": ObjectId(roast_id), "archived": {"$ne": True}}
    )
    if not roast:
        return {"success": False, "error": "Roast not found"}, 404
    if get_roast_lifecycle_status(roast) != ROAST_LIFECYCLE_DRAFT:
        return {
            "success": False,
            "error": "Only draft roasts can be started",
        }, 409

    current_time = get_current_time_with_tz()
    update_data = {
        "roast_start_time": current_time,
        "lifecycle_status": ROAST_LIFECYCLE_STARTED,
        "updated_at": current_time,
    }
    if data.get("bean_id"):
        update_data["bean_id"] = ObjectId(data["bean_id"])
    if data.get("original_weight_grams"):
        weight = int(data["original_weight_grams"])
        update_data["original_weight_grams"] = weight
        if data.get("bean_id"):
            get_beans_collection().update_one(
                {"_id": ObjectId(data["bean_id"])},
                {
                    "$inc": {"stock_grams": -weight},
                    "$set": {"updated_at": current_time},
                },
            )
    if data.get("ambient_temp_celsius"):
        update_data["ambient_temp_celsius"] = float(data["ambient_temp_celsius"])
    if data.get("ambient_humidity"):
        update_data["ambient_humidity"] = float(data["ambient_humidity"])
    roasts.update_one({"_id": ObjectId(roast_id)}, {"$set": update_data})
    return {"success": True}, 200


def end_roast(roast_id, data):
    roasts = get_roasts_collection()
    roast = roasts.find_one({"_id": ObjectId(roast_id)})
    if not roast:
        return {"success": False, "error": "Roast not found"}, 404
    if get_roast_lifecycle_status(roast) != ROAST_LIFECYCLE_STARTED:
        return {
            "success": False,
            "error": "Only started roasts can be ended",
        }, 409

    end_time = get_current_time_with_tz()
    elapsed_seconds = 0
    if roast.get("roast_start_time"):
        if data.get("elapsed_seconds") is not None:
            elapsed_seconds = int(data["elapsed_seconds"])
        else:
            start_time = roast["roast_start_time"]
            if start_time.tzinfo is None:
                start_time = get_local_timezone().localize(start_time)
            elapsed_seconds = int((end_time - start_time).total_seconds())
        elapsed_seconds = max(
            0,
            min(current_app.config["MAX_ROAST_TIME_SECONDS"], elapsed_seconds),
        )

        temperature = fetch_temperature_from_sensor()
        last_fan = 0
        last_power = 0
        if roast.get("temp_curve"):
            last_entry = roast["temp_curve"][-1]
            last_fan = last_entry.get("fan_setting", 0)
            last_power = last_entry.get("power_setting", 0)
        if temperature is not None:
            roasts.update_one(
                {"_id": ObjectId(roast_id)},
                {
                    "$push": {
                        "temp_curve": {
                            "time_seconds": elapsed_seconds,
                            "temperature": float(temperature),
                            "fan_setting": last_fan,
                            "power_setting": last_power,
                        }
                    },
                    "$set": {"updated_at": end_time},
                },
            )

        drop_event = {"event_name": "Drop", "time_seconds": elapsed_seconds}
        if temperature is not None:
            drop_event["temperature"] = float(temperature)
        if last_fan:
            drop_event["fan_setting"] = last_fan
        if last_power:
            drop_event["power_setting"] = last_power
        roasts.update_one(
            {"_id": ObjectId(roast_id)},
            {
                "$push": {"key_timings": drop_event},
                "$set": {"updated_at": end_time},
            },
        )

    roasts.update_one(
        {"_id": ObjectId(roast_id)},
        {
            "$set": {
                "roast_end_time": end_time,
                "lifecycle_status": ROAST_LIFECYCLE_COMPLETED,
                "updated_at": end_time,
            }
        },
    )
    return {"success": True}, 200


def update_roast_setup(roast_id, data):
    roasts = get_roasts_collection()
    roast = roasts.find_one(
        {"_id": ObjectId(roast_id), "archived": {"$ne": True}}
    )
    if not roast:
        return {"success": False, "error": "Roast not found"}, 404
    if get_roast_lifecycle_status(roast) != ROAST_LIFECYCLE_DRAFT:
        return {
            "success": False,
            "error": "Setup can only be changed before the roast starts",
        }, 409

    update_data = {"updated_at": get_current_time_with_tz()}
    unset_data = {}
    if "title" in data:
        update_data["title"] = (data.get("title") or "").strip() or "Untitled Roast"
    if "bean_id" in data:
        if data.get("bean_id"):
            update_data["bean_id"] = ObjectId(data["bean_id"])
        else:
            unset_data["bean_id"] = ""
    if "original_weight_grams" in data:
        if data.get("original_weight_grams"):
            update_data["original_weight_grams"] = int(
                data["original_weight_grams"]
            )
        else:
            unset_data["original_weight_grams"] = ""
    if "ambient_temp_celsius" in data:
        value = data.get("ambient_temp_celsius")
        update_data["ambient_temp_celsius"] = (
            float(value) if value not in (None, "") else None
        )
    if "ambient_humidity" in data:
        value = data.get("ambient_humidity")
        update_data["ambient_humidity"] = (
            float(value) if value not in (None, "") else None
        )

    operation = {"$set": update_data}
    if unset_data:
        operation["$unset"] = unset_data
    roasts.update_one({"_id": ObjectId(roast_id)}, operation)
    return {"success": True}, 200


def complete_draft(roast_id):
    roasts = get_roasts_collection()
    roast = roasts.find_one(
        {"_id": ObjectId(roast_id), "archived": {"$ne": True}}
    )
    if not roast:
        return {"success": False, "error": "Roast not found"}, 404
    if get_roast_lifecycle_status(roast) != ROAST_LIFECYCLE_DRAFT:
        return {
            "success": False,
            "error": "Only draft roasts can be manually completed",
        }, 409
    current_time = get_current_time_with_tz()
    roasts.update_one(
        {"_id": ObjectId(roast_id)},
        {
            "$set": {
                "lifecycle_status": ROAST_LIFECYCLE_COMPLETED,
                "updated_at": current_time,
            }
        },
    )
    return {
        "success": True,
        "lifecycle_status": ROAST_LIFECYCLE_COMPLETED,
    }, 200
