"""Audited, read-only Settings sync preflight adapter."""

from __future__ import annotations

from pathlib import Path

from roastlogger.services.database_sync_audit import (
    git_provenance,
    utc_text,
    write_ui_intent_audit,
)
from roastlogger.services.database_sync_plan import (
    SyncRuntime,
    SyncSafetyError,
    build_preflight,
    endpoint_descriptor,
    new_run_id,
    sanitize_failure,
    validate_device,
)


def _fallback_device(values) -> str:
    try:
        return validate_device(values.get("DEVICE"))
    except Exception:
        return "unconfigured"


def _fallback_descriptors(values, direction):
    if direction == "online-to-local":
        roles = (
            ("online", "MONGO_URI", "ONLINE_DB_NAME"),
            ("local", "MONGO_URI_LOCAL", "LOCAL_DB_NAME"),
        )
    else:
        roles = (
            ("local", "MONGO_URI_LOCAL", "LOCAL_DB_NAME"),
            ("online", "MONGO_URI", "ONLINE_DB_NAME"),
        )
    return tuple(
        endpoint_descriptor(
            values.get(uri_key, ""),
            role,
            values.get(database_key, "roastlogger"),
        )
        for role, uri_key, database_key in roles
    )


def run_ui_preflight(
    values,
    connections,
    root: Path,
    direction: str,
    *,
    preflight=build_preflight,
    audit_writer=write_ui_intent_audit,
    blocked_error=None,
):
    root = Path(root)
    run_id = new_run_id()
    timestamp = utc_text()
    runtime = None
    plan = None
    failure = None
    if blocked_error:
        failure = sanitize_failure(SyncSafetyError(blocked_error))
    else:
        try:
            runtime = SyncRuntime.from_mapping(values, direction=direction)
            source_client = (
                connections.online_client
                if runtime.source_role == "online"
                else connections.local_client
            )
            destination_client = (
                connections.online_client
                if runtime.destination_role == "online"
                else connections.local_client
            )
            plan = preflight(
                runtime,
                source_client,
                destination_client,
                root,
                run_id=run_id,
            )
        except Exception as error:
            failure = sanitize_failure(error)

    if runtime:
        source = runtime.source_descriptor
        destination = runtime.destination_descriptor
        device = runtime.device
    else:
        source, destination = _fallback_descriptors(values, direction)
        device = _fallback_device(values)

    record = {
        "schema_version": 1,
        "trigger": "settings_ui",
        "event": "sync_button_clicked",
        "run_id": run_id,
        "timestamp": timestamp,
        "DEVICE": device,
        "direction": direction,
        "source": source,
        "destination": destination,
        "git": git_provenance(root),
        "preflight": {
            "status": "success" if plan else "failed",
            "plan": plan,
            "failure": failure,
        },
    }
    try:
        audit_path = audit_writer(
            root,
            run_id=run_id,
            device=device,
            direction=direction,
            record=record,
        )
    except Exception as error:
        return {
            "success": False,
            "run_id": run_id,
            "plan": plan,
            "error": failure,
            "audit_recorded": False,
            "audit_error": sanitize_failure(error),
        }

    return {
        "success": plan is not None,
        "run_id": run_id,
        "plan": plan,
        "error": failure,
        "audit_recorded": True,
        "audit_path": str(audit_path.relative_to(root)),
    }
