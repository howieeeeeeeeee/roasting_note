"""Settings, database synchronization, and cleanup routes."""

from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlsplit

from bson.objectid import ObjectId
from flask import Blueprint, current_app, jsonify, request, session

from roastlogger.config import DEFAULT_TEMP_SENSOR_URL
from roastlogger.database import get_connections, get_current_db_mode
from roastlogger.routing import register_unprefixed_routes
from roastlogger.services.database_backup import backup_destination_database
from roastlogger.services.database_sync_plan import build_preflight, sanitize_failure
from roastlogger.services.database_sync_runner import synchronize_collections
from roastlogger.services.database_sync_ui import run_ui_preflight
from roastlogger.services.database_sync_web import (
    PreviewRegistry,
    WebSyncError,
    WebSyncService,
)


blueprint = Blueprint("settings", __name__)


def _is_loopback(value):
    candidate = (value or "").split("%", 1)[0].strip().lower()
    if candidate == "localhost":
        return True
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def _host_is_loopback():
    try:
        parsed = urlsplit(f"//{request.host}")
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return False
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        return False
    return _is_loopback(hostname)


def _request_is_direct_loopback():
    return _is_loopback(request.remote_addr) and _host_is_loopback()


def _normalized_origin(value):
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return None
    if port is None:
        port = 443 if parsed.scheme.lower() == "https" else 80
    return parsed.scheme.lower(), parsed.hostname.lower(), port


def _same_origin_request():
    supplied = request.headers.get("Origin")
    if not supplied:
        return True
    return _normalized_origin(supplied) == _normalized_origin(request.host_url)


def _e2e_sync_executor():
    executor = current_app.config.get("E2E_SYNC_EXECUTOR")
    return executor if current_app.config.get("E2E_MODE") else None


def _browser_apply_allowed():
    if not _request_is_direct_loopback():
        return False
    if current_app.config.get("E2E_MODE"):
        return _e2e_sync_executor() is not None
    return True


def _sync_root():
    if current_app.config.get("E2E_MODE"):
        return current_app.config["E2E_ARTIFACT_ROOT"]
    return current_app.config["REPOSITORY_ROOT"]


def _preview_registry():
    return current_app.extensions.setdefault(
        "database_sync_previews", PreviewRegistry()
    )


def _web_sync_service():
    executor = _e2e_sync_executor()
    return WebSyncService(
        current_app.config,
        get_connections(),
        _sync_root(),
        _preview_registry(),
        backup=(executor.backup if executor else backup_destination_database),
        synchronize=(
            executor.synchronize if executor else synchronize_collections
        ),
    )


def _phase_guard(*, require_json):
    if not _request_is_direct_loopback():
        return jsonify(
            {
                "success": False,
                "error": "Browser-applied sync requires a direct loopback peer and host",
            }
        ), 403
    if current_app.config.get("E2E_MODE") and _e2e_sync_executor() is None:
        return jsonify(
            {
                "success": False,
                "error": "Browser-applied sync is disabled in ordinary E2E mode",
            }
        ), 409
    if require_json and not request.is_json:
        return jsonify(
            {
                "success": False,
                "error": "Browser-applied sync requires application/json",
            }
        ), 415
    if require_json and not _same_origin_request():
        return jsonify(
            {
                "success": False,
                "error": "Browser-applied sync requires a same-origin request",
            }
        ), 403
    return None


def _phase_payload(allowed):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) - set(allowed):
        raise WebSyncError("sync request payload is invalid")
    return data


def _phase_error(error):
    if isinstance(error, WebSyncError):
        body = {
            "success": False,
            "error": str(error),
            "stage": error.stage,
            "run_id": error.run_id,
        }
        return jsonify(body), error.status_code
    return jsonify(
        {
            "success": False,
            "error": sanitize_failure(error)["message"],
            "stage": "recovery_required",
        }
    ), 500


def api_get_db_settings():
    result = {
        "mode": get_current_db_mode(),
        "default": current_app.config["DEFAULT_DB"],
        "e2e_mode": bool(current_app.config.get("E2E_MODE")),
    }
    if result["e2e_mode"]:
        result.update(
            {
                "local_database": current_app.config["LOCAL_DB_NAME"],
                "test_run_id": current_app.config["E2E_RUN_ID"],
            }
        )
    return jsonify(result)


def api_set_db_settings():
    data = request.get_json() or {}
    mode = data.get("mode", "local")
    if current_app.config.get("E2E_MODE") and mode != "local":
        return (
            jsonify(
                {
                    "success": False,
                    "error": "E2E mode is locked to the local E2E database",
                }
            ),
            409,
        )
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
    return _sync_route_disabled()


def api_sync_local_to_online():
    return _sync_route_disabled()


def _sync_route_disabled():
    e2e_mode = current_app.config.get("E2E_MODE")
    return (
        jsonify(
            {
                "success": False,
                "error": (
                    "Database sync is disabled in E2E mode"
                    if e2e_mode
                    else "Legacy one-request database sync is disabled"
                ),
                "guidance": (
                    "Use guarded local Settings or scripts/sync_database.py; "
                    "both require backup and apply confirmations."
                ),
            }
        ),
        409,
    )


def api_sync_preflight(direction):
    e2e_mode = current_app.config.get("E2E_MODE")
    executor = _e2e_sync_executor()
    result = run_ui_preflight(
        current_app.config,
        get_connections(),
        _sync_root(),
        direction,
        preflight=executor.preflight if executor else build_preflight,
        blocked_error=(
            "Database sync preflight is disabled in E2E mode"
            if e2e_mode and executor is None
            else None
        ),
        apply_eligible=_browser_apply_allowed(),
    )
    if not result["audit_recorded"]:
        return jsonify(result), 500
    if result["success"] and result["apply_eligible"]:
        _web_sync_service().register_preview(result["plan"])
    return jsonify(result), 200 if result["success"] else 503


def api_sync_active_run():
    guarded = _phase_guard(require_json=False)
    if guarded:
        return guarded
    try:
        state = _web_sync_service().active()
        return jsonify({"success": True, "active": state})
    except Exception as error:
        return _phase_error(error)


def api_sync_backup(run_id):
    guarded = _phase_guard(require_json=True)
    if guarded:
        return guarded
    try:
        data = _phase_payload({"direction", "confirmation"})
        result = _web_sync_service().backup(
            run_id,
            data.get("direction"),
            data.get("confirmation"),
        )
        return jsonify(result), 200 if result["success"] else 500
    except Exception as error:
        return _phase_error(error)


def api_sync_apply(run_id):
    guarded = _phase_guard(require_json=True)
    if guarded:
        return guarded
    try:
        data = _phase_payload({"direction", "confirmation"})
        result = _web_sync_service().apply(
            run_id,
            data.get("direction"),
            data.get("confirmation"),
        )
        return jsonify(result), 200 if result["success"] else 500
    except Exception as error:
        return _phase_error(error)


def api_sync_cancel(run_id):
    guarded = _phase_guard(require_json=True)
    if guarded:
        return guarded
    try:
        data = _phase_payload({"direction"})
        result = _web_sync_service().cancel(run_id, data.get("direction"))
        return jsonify(result), 200 if result["success"] else 500
    except Exception as error:
        return _phase_error(error)


def api_clean_test_data():
    if current_app.config.get("E2E_MODE"):
        return _e2e_cleanup_disabled()
    local_db = get_connections().local_db
    try:
        beans_deleted = local_db.beans.delete_many(
            {"test_data": True}
        ).deleted_count
        roasts_deleted = local_db.roasts.delete_many(
            {"test_data": True}
        ).deleted_count
        temp_logs_deleted = 0
        temp_logs_dir = current_app.config["TEMP_LOG_DIR"]
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
    if current_app.config.get("E2E_MODE"):
        return _e2e_cleanup_disabled()
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


def _e2e_cleanup_disabled():
    return (
        jsonify(
            {
                "success": False,
                "error": "Use run-scoped E2E cleanup for this test runtime",
            }
        ),
        409,
    )


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
            "/api/sync/preflight/<direction>",
            "api_sync_preflight",
            api_sync_preflight,
            ["POST"],
        ),
        (
            "/api/sync/runs/active",
            "api_sync_active_run",
            api_sync_active_run,
            ["GET"],
        ),
        (
            "/api/sync/runs/<run_id>/backup",
            "api_sync_backup",
            api_sync_backup,
            ["POST"],
        ),
        (
            "/api/sync/runs/<run_id>/apply",
            "api_sync_apply",
            api_sync_apply,
            ["POST"],
        ),
        (
            "/api/sync/runs/<run_id>/cancel",
            "api_sync_cancel",
            api_sync_cancel,
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
