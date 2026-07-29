"""Sanitized database-sync configuration and preflight planning."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


KNOWN_COLLECTIONS = ("beans", "roasts")
DIRECTIONS = ("online-to-local", "local-to-online")
DEVICE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
DATABASE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")


class SyncSafetyError(ValueError):
    """A credential-free configuration or preflight error."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_run_id(now=None) -> str:
    current = now or utc_now()
    return f"{current.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def validate_device(device: str | None) -> str:
    value = (device or "").strip()
    if not value:
        raise SyncSafetyError("DEVICE is required")
    if not DEVICE_PATTERN.fullmatch(value):
        raise SyncSafetyError(
            "DEVICE must use 1-64 letters, digits, underscores, or hyphens"
        )
    return value


def validate_batch_size(batch_size: int) -> int:
    if isinstance(batch_size, bool) or batch_size <= 0:
        raise SyncSafetyError("batch size must be a positive integer")
    return batch_size


def validate_database_name(database_name: str | None) -> str:
    value = (database_name or "").strip()
    if not DATABASE_PATTERN.fullmatch(value) or value in {".", ".."}:
        raise SyncSafetyError("database name is unsafe")
    return value


def resolve_collections(requested=None) -> tuple[str, ...]:
    values = tuple(requested or KNOWN_COLLECTIONS)
    unknown = sorted(set(values) - set(KNOWN_COLLECTIONS))
    if unknown:
        raise SyncSafetyError(
            "unknown sync collections: " + ", ".join(unknown)
        )
    if not values:
        raise SyncSafetyError("at least one sync collection is required")
    return tuple(dict.fromkeys(values))


def endpoint_identity(uri: str, database_name: str) -> tuple[str, str, str]:
    parsed = urlsplit(uri)
    host = parsed.netloc.rsplit("@", 1)[-1].lower()
    return parsed.scheme.lower(), host, database_name


def endpoint_descriptor(uri: str, role: str, database_name: str) -> dict:
    parsed = urlsplit(uri)
    host = parsed.netloc.rsplit("@", 1)[-1]
    return {
        "role": role,
        "host": host or "configured-endpoint",
        "database": database_name,
    }


def sanitize_failure(error: Exception) -> dict:
    if isinstance(error, SyncSafetyError):
        return {"type": error.__class__.__name__, "message": str(error)}
    return {
        "type": error.__class__.__name__,
        "message": "database operation failed; inspect local diagnostics",
    }


@dataclass(frozen=True)
class SyncRuntime:
    direction: str
    device: str
    batch_size: int
    requested_collections: tuple[str, ...]
    source_role: str
    destination_role: str
    source_uri: str
    destination_uri: str
    source_database_name: str
    destination_database_name: str

    @classmethod
    def from_mapping(
        cls,
        values,
        *,
        direction,
        collections=None,
        batch_size=500,
    ):
        if direction not in DIRECTIONS:
            raise SyncSafetyError(f"unsupported direction: {direction}")
        device = validate_device(values.get("DEVICE"))
        batch_size = validate_batch_size(batch_size)
        requested = resolve_collections(collections)
        if direction == "online-to-local":
            source_role, destination_role = "online", "local"
            source_uri, destination_uri = (
                values.get("MONGO_URI", ""),
                values.get("MONGO_URI_LOCAL", ""),
            )
            source_db, destination_db = (
                validate_database_name(
                    values.get("ONLINE_DB_NAME", "roastlogger")
                ),
                validate_database_name(
                    values.get("LOCAL_DB_NAME", "roastlogger")
                ),
            )
        else:
            source_role, destination_role = "local", "online"
            source_uri, destination_uri = (
                values.get("MONGO_URI_LOCAL", ""),
                values.get("MONGO_URI", ""),
            )
            source_db, destination_db = (
                validate_database_name(
                    values.get("LOCAL_DB_NAME", "roastlogger")
                ),
                validate_database_name(
                    values.get("ONLINE_DB_NAME", "roastlogger")
                ),
            )
        if not source_uri or not destination_uri:
            raise SyncSafetyError("both database endpoints are required")
        if endpoint_identity(source_uri, source_db) == endpoint_identity(
            destination_uri,
            destination_db,
        ):
            raise SyncSafetyError(
                "source and destination resolve to the same endpoint and database"
            )
        return cls(
            direction=direction,
            device=device,
            batch_size=batch_size,
            requested_collections=requested,
            source_role=source_role,
            destination_role=destination_role,
            source_uri=source_uri,
            destination_uri=destination_uri,
            source_database_name=source_db,
            destination_database_name=destination_db,
        )

    @property
    def source_descriptor(self):
        return endpoint_descriptor(
            self.source_uri,
            self.source_role,
            self.source_database_name,
        )

    @property
    def destination_descriptor(self):
        return endpoint_descriptor(
            self.destination_uri,
            self.destination_role,
            self.destination_database_name,
        )


def planned_backup_path(root: Path, runtime: SyncRuntime, run_id: str) -> Path:
    timestamp = run_id.split("-", 1)[0]
    origin = (
        f"local--{runtime.device}"
        if runtime.destination_role == "local"
        else "online"
    )
    return (
        root
        / "db_backup"
        / "database_mirrors"
        / origin
        / runtime.destination_database_name
        / f"{timestamp}__{run_id}"
    )


def planned_audit_path(root: Path, runtime: SyncRuntime, run_id: str) -> Path:
    timestamp = run_id.split("-", 1)[0]
    return (
        root
        / "docs"
        / "audit_history"
        / "database_mirrors"
        / timestamp[:4]
        / timestamp[4:6]
        / f"{timestamp}__{runtime.device}__{runtime.direction}__{run_id}.json"
    )


def _ping(client, role):
    try:
        client.admin.command("ping")
    except Exception as error:
        raise SyncSafetyError(f"{role} endpoint is unavailable") from error


def build_preflight(
    runtime: SyncRuntime,
    source_client,
    destination_client,
    root: Path,
    *,
    run_id=None,
):
    run_id = run_id or new_run_id()
    _ping(source_client, runtime.source_role)
    _ping(destination_client, runtime.destination_role)
    source_db = source_client[runtime.source_database_name]
    destination_db = destination_client[runtime.destination_database_name]
    try:
        source_counts = {
            name: source_db[name].count_documents(
                {"archived": {"$ne": True}}
            )
            for name in runtime.requested_collections
        }
        destination_counts = {
            name: destination_db[name].count_documents({})
            for name in runtime.requested_collections
        }
        backup_collections = sorted(destination_db.list_collection_names())
        backup_counts = {
            name: destination_db[name].count_documents({})
            for name in backup_collections
        }
    except Exception as error:
        raise SyncSafetyError(
            "collection counts are unavailable for preflight"
        ) from error

    return {
        "schema_version": 1,
        "run_id": run_id,
        "device": runtime.device,
        "direction": runtime.direction,
        "source": runtime.source_descriptor,
        "destination": runtime.destination_descriptor,
        "requested_collections": list(runtime.requested_collections),
        "resolved_collections": list(runtime.requested_collections),
        "batch_size": runtime.batch_size,
        "source_counts": source_counts,
        "destination_counts": destination_counts,
        "backup": {
            "scope": "complete_destination_database",
            "collections": backup_collections,
            "counts": backup_counts,
            "path": str(planned_backup_path(root, runtime, run_id)),
        },
        "audit_path": str(planned_audit_path(root, runtime, run_id)),
        "cli_command": (
            "uv run python scripts/sync_database.py "
            f"--direction {runtime.direction}"
        ),
    }
