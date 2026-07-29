"""Restorable, streaming destination database backups for guarded sync."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util

from roastlogger.services.database_sync_plan import (
    SyncRuntime,
    planned_backup_path,
    sanitize_failure,
)


def utc_text(value=None) -> str:
    current = value or datetime.now(timezone.utc)
    return current.isoformat().replace("+00:00", "Z")


def encode_collection_name(name: str) -> str:
    encoded = base64.urlsafe_b64encode(name.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def decode_collection_name(encoded: str) -> str:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding).decode("utf-8")


def _atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with temporary.open("x", encoding="utf-8") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def _stream_collection(collection, path: Path) -> dict:
    temporary = path.with_name(f".{path.name}.tmp")
    digest = hashlib.sha256()
    count = 0
    byte_count = 0
    try:
        with temporary.open("xb") as output:
            for document in collection.find({}):
                line = (
                    json_util.dumps(
                        document,
                        json_options=json_util.CANONICAL_JSON_OPTIONS,
                    ).encode("utf-8")
                    + b"\n"
                )
                output.write(line)
                digest.update(line)
                byte_count += len(line)
                count += 1
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "documents": count,
        "bytes": byte_count,
        "sha256": digest.hexdigest(),
    }


def _manifest_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup_destination_database(
    runtime: SyncRuntime,
    destination_client,
    root: Path,
    run_id: str,
) -> dict:
    """Back up every destination collection and finalize only when complete."""
    final_path = planned_backup_path(root, runtime, run_id)
    partial_path = final_path.with_name(f"{final_path.name}.partial")
    if final_path.exists() or partial_path.exists():
        raise FileExistsError("backup path already exists for this run")
    partial_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path.mkdir()

    started_at = utc_text()
    entries = []
    try:
        destination_db = destination_client[runtime.destination_database_name]
        collection_names = sorted(destination_db.list_collection_names())
        for collection_name in collection_names:
            filename = f"{encode_collection_name(collection_name)}.jsonl"
            details = _stream_collection(
                destination_db[collection_name],
                partial_path / filename,
            )
            entries.append(
                {
                    "name": collection_name,
                    "filename": filename,
                    **details,
                }
            )

        manifest = {
            "schema_version": 1,
            "extended_json_mode": "canonical",
            "run_id": run_id,
            "reason": "guarded_database_sync_destination_backup",
            "destination": {
                "role": runtime.destination_role,
                "database": runtime.destination_database_name,
            },
            "device": runtime.device,
            "started_at": started_at,
            "completed_at": utc_text(),
            "status": "complete",
            "collections": entries,
            "collection_count": len(entries),
            "document_count": sum(item["documents"] for item in entries),
        }
        _atomic_json(partial_path / "manifest.json", manifest)
        os.replace(partial_path, final_path)
        manifest_path = final_path / "manifest.json"
        return {
            "path": str(final_path),
            "manifest_path": str(manifest_path),
            "manifest_sha256": _manifest_digest(manifest_path),
            "status": "complete",
            "collection_count": manifest["collection_count"],
            "document_count": manifest["document_count"],
            "collections": entries,
        }
    except Exception as error:
        failure = {
            "schema_version": 1,
            "run_id": run_id,
            "status": "incomplete",
            "destination": {
                "role": runtime.destination_role,
                "database": runtime.destination_database_name,
            },
            "device": runtime.device,
            "started_at": started_at,
            "ended_at": utc_text(),
            "completed_collections": entries,
            "failure": sanitize_failure(error),
        }
        try:
            _atomic_json(partial_path / "failure.json", failure)
        except Exception:
            pass
        raise
