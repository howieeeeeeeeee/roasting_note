"""Two-confirmation guarded execution for timestamp-aware database sync."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from roastlogger.services.database_backup import backup_destination_database
from roastlogger.services.database_sync import sync_collection
from roastlogger.services.database_sync_audit import (
    git_provenance,
    utc_text,
    write_applied_audit,
    write_recovery_audit,
)
from roastlogger.services.database_sync_plan import sanitize_failure


class SyncExecutionError(RuntimeError):
    def __init__(self, collection, completed, cause):
        super().__init__(f"sync failed for collection: {collection}")
        self.collection = collection
        self.completed = completed
        self.__cause__ = cause


def _aggregate(results: dict) -> dict:
    fields = ("added", "updated", "skipped", "conflicts")
    return {
        field: sum(item[field] for item in results.values())
        for field in fields
    }


def synchronize_collections(runtime, source_client, destination_client):
    source_db = source_client[runtime.source_database_name]
    destination_db = destination_client[runtime.destination_database_name]
    results = {}
    for name in runtime.requested_collections:
        try:
            result = sync_collection(
                source_db[name],
                destination_db[name],
                batch_size=runtime.batch_size,
            )
            result["post_run_count"] = destination_db[name].count_documents({})
            results[name] = result
        except Exception as error:
            raise SyncExecutionError(name, results, error) from error
    return {
        "collections": results,
        "aggregate": _aggregate(results),
        "verified": True,
    }


def _base_audit(runtime, plan, started_at):
    return {
        "schema_version": 1,
        "trigger": "guarded_cli",
        "run_id": plan["run_id"],
        "status": "started",
        "started_at": utc_text(started_at),
        "DEVICE": runtime.device,
        "direction": runtime.direction,
        "source": plan["source"],
        "destination": plan["destination"],
        "sync_mode": "timestamp_aware",
        "batch_size": runtime.batch_size,
        "requested_collections": list(runtime.requested_collections),
        "resolved_collections": plan["resolved_collections"],
        "preflight": {
            "source_counts": plan["source_counts"],
            "destination_counts": plan["destination_counts"],
        },
        "backup": {
            "path": plan["backup"]["path"],
            "status": "not_started",
        },
        "git": None,
    }


def _finish_record(root, record, status, started_at, **values):
    ended_at = datetime.now(timezone.utc)
    record.update(values)
    record.update(
        {
            "status": status,
            "ended_at": utc_text(ended_at),
            "duration_seconds": max(
                0,
                round((ended_at - started_at).total_seconds(), 3),
            ),
            "git": git_provenance(root),
        }
    )
    return record


def _persist_record(root, runtime, plan, record, activity_started):
    try:
        path = write_applied_audit(root, runtime, plan["run_id"], record)
        return {
            "audit_path": str(path),
            "recovery_path": None,
            "audit_error": None,
        }
    except Exception as error:
        if not activity_started:
            raise
        recovery_root = Path(record["backup"]["path"])
        if (
            record["backup"]["status"] != "complete"
            and not recovery_root.name.endswith(".partial")
        ):
            recovery_root = recovery_root.with_name(
                f"{recovery_root.name}.partial"
            )
        recovery_path = write_recovery_audit(recovery_root, record)
        return {
            "audit_path": None,
            "recovery_path": str(recovery_path),
            "audit_error": sanitize_failure(error),
        }


def run_guarded_sync(
    runtime,
    source_client,
    destination_client,
    root: Path,
    plan: dict,
    *,
    prompt=input,
    backup=backup_destination_database,
    synchronize=synchronize_collections,
):
    """Apply one run; callers must print the preflight before invoking this."""
    started_at = datetime.now(timezone.utc)
    record = _base_audit(runtime, plan, started_at)
    run_id = plan["run_id"]
    try:
        first = prompt(f"Type BACKUP {run_id}: ")
    except EOFError:
        first = ""
    if first != f"BACKUP {run_id}":
        return {
            "status": "cancelled_before_backup",
            "exit_code": 1,
            "audit_path": None,
        }

    try:
        backup_result = backup(
            runtime,
            destination_client,
            root,
            run_id,
        )
        record["backup"] = backup_result
    except Exception as error:
        backup_path = Path(plan["backup"]["path"])
        record["backup"] = {
            "path": str(
                backup_path.with_name(f"{backup_path.name}.partial")
            ),
            "status": "incomplete",
        }
        record = _finish_record(
            root,
            record,
            "backup_failed",
            started_at,
            failure=sanitize_failure(error),
        )
        persisted = _persist_record(
            root,
            runtime,
            plan,
            record,
            activity_started=True,
        )
        return {"status": "backup_failed", "exit_code": 1, **persisted}

    try:
        second = prompt(f"Type APPLY {runtime.direction} {run_id}: ")
    except EOFError:
        second = ""
    if second != f"APPLY {runtime.direction} {run_id}":
        record = _finish_record(
            root,
            record,
            "cancelled_after_backup",
            started_at,
            cancellation={"stage": "after_backup"},
        )
        persisted = _persist_record(
            root,
            runtime,
            plan,
            record,
            activity_started=True,
        )
        return {
            "status": "cancelled_after_backup",
            "exit_code": 1,
            **persisted,
        }

    try:
        sync_result = synchronize(
            runtime,
            source_client,
            destination_client,
        )
        record = _finish_record(
            root,
            record,
            "success",
            started_at,
            sync=sync_result,
        )
        status = "success"
        exit_code = 0
    except Exception as error:
        completed = getattr(error, "completed", {})
        partial_result = {
            "collections": completed,
            "aggregate": _aggregate(completed),
            "verified": False,
            "failed_collection": getattr(error, "collection", None),
        }
        record = _finish_record(
            root,
            record,
            "partial_sync_failed",
            started_at,
            sync=partial_result,
            failure=sanitize_failure(error),
        )
        status = "partial_sync_failed"
        exit_code = 1

    persisted = _persist_record(
        root,
        runtime,
        plan,
        record,
        activity_started=True,
    )
    if persisted["audit_error"]:
        exit_code = 2
        status = f"{status}_audit_recovery"
    return {
        "status": status,
        "exit_code": exit_code,
        "sync": record.get("sync"),
        **persisted,
    }
