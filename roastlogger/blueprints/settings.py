"""Settings, database synchronization, and cleanup routes."""

from __future__ import annotations

import os

from bson.objectid import ObjectId
from flask import Blueprint, current_app, jsonify, request, session

from roastlogger.config import DEFAULT_TEMP_SENSOR_URL
from roastlogger.database import get_connections, get_current_db_mode
from roastlogger.routing import register_unprefixed_routes
from roastlogger.services.database_sync import sync_collection


blueprint = Blueprint("settings", __name__)


def api_get_db_settings():
    return jsonify(
        {
            "mode": get_current_db_mode(),
            "default": current_app.config["DEFAULT_DB"],
        }
    )


def api_set_db_settings():
    data = request.get_json() or {}
    mode = data.get("mode", "local")
    if mode not in ["local", "online"]:
        return jsonify({"success": False, "error": "Invalid mode"}), 400
    session["db_mode"] = mode
    return jsonify({"success": True, "mode": mode})


def api_get_sensor_settings():
    return jsonify(
        {
            "url": session.get(
                "temp_sensor_url",
                current_app.config["TEMP_SENSOR_URL"],
            ),
            "default": DEFAULT_TEMP_SENSOR_URL,
        }
    )


def api_set_sensor_settings():
    data = request.get_json() or {}
    url = data.get("url", "").strip() or DEFAULT_TEMP_SENSOR_URL
    session["temp_sensor_url"] = url
    return jsonify({"success": True, "url": url})


def api_sync_online_to_local():
    connections = get_connections()
    try:
        beans_result = sync_collection(
            connections.online_db.beans,
            connections.local_db.beans,
        )
        roasts_result = sync_collection(
            connections.online_db.roasts,
            connections.local_db.roasts,
        )
        return jsonify(
            {"success": True, "beans": beans_result, "roasts": roasts_result}
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


def api_sync_local_to_online():
    connections = get_connections()
    try:
        beans_result = sync_collection(
            connections.local_db.beans,
            connections.online_db.beans,
        )
        roasts_result = sync_collection(
            connections.local_db.roasts,
            connections.online_db.roasts,
        )
        return jsonify(
            {"success": True, "beans": beans_result, "roasts": roasts_result}
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


def api_clean_test_data():
    local_db = get_connections().local_db
    try:
        beans_deleted = local_db.beans.delete_many(
            {"test_data": True}
        ).deleted_count
        roasts_deleted = local_db.roasts.delete_many(
            {"test_data": True}
        ).deleted_count
        temp_logs_deleted = 0
        temp_logs_dir = os.path.join(os.getcwd(), "temp_logs")
        if os.path.exists(temp_logs_dir):
            for filename in os.listdir(temp_logs_dir):
                if not filename.endswith(".csv"):
                    continue
                filepath = os.path.join(temp_logs_dir, filename)
                roast_id = filename.replace(".csv", "")
                try:
                    roast = local_db.roasts.find_one(
                        {"_id": ObjectId(roast_id)}
                    )
                    if roast is None:
                        os.remove(filepath)
                        temp_logs_deleted += 1
                except Exception:
                    pass
        return jsonify(
            {
                "success": True,
                "beans_deleted": beans_deleted,
                "roasts_deleted": roasts_deleted,
                "temp_logs_deleted": temp_logs_deleted,
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


def api_clean_local_db():
    local_db = get_connections().local_db
    try:
        beans_deleted = local_db.beans.delete_many({}).deleted_count
        roasts_deleted = local_db.roasts.delete_many({}).deleted_count
        return jsonify(
            {
                "success": True,
                "beans_deleted": beans_deleted,
                "roasts_deleted": roasts_deleted,
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


register_unprefixed_routes(
    blueprint,
    [
        ("/api/settings/db", "api_get_db_settings", api_get_db_settings, ["GET"]),
        ("/api/settings/db", "api_set_db_settings", api_set_db_settings, ["POST"]),
        (
            "/api/settings/sensor",
            "api_get_sensor_settings",
            api_get_sensor_settings,
            ["GET"],
        ),
        (
            "/api/settings/sensor",
            "api_set_sensor_settings",
            api_set_sensor_settings,
            ["POST"],
        ),
        (
            "/api/sync/online-to-local",
            "api_sync_online_to_local",
            api_sync_online_to_local,
            ["POST"],
        ),
        (
            "/api/sync/local-to-online",
            "api_sync_local_to_online",
            api_sync_local_to_online,
            ["POST"],
        ),
        (
            "/api/db/clean-test-data",
            "api_clean_test_data",
            api_clean_test_data,
            ["POST"],
        ),
        (
            "/api/db/clean-local",
            "api_clean_local_db",
            api_clean_local_db,
            ["POST"],
        ),
    ],
)
