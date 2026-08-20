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


class BackupVerificationError(RuntimeError):
    """A completed backup no longer matches its trusted run identity."""


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


def _payload_details(path: Path) -> dict:
    digest = hashlib.sha256()
    byte_count = 0
    document_count = 0
    with path.open("rb") as payload:
        for line in payload:
            digest.update(line)
            byte_count += len(line)
            document_count += 1
    return {
        "sha256": digest.hexdigest(),
        "bytes": byte_count,
        "documents": document_count,
    }


def verify_backup_result(
    runtime: SyncRuntime,
    root: Path,
    run_id: str,
    result: dict,
) -> dict:
    """Verify a complete backup manifest and every payload before apply."""
    expected_path = planned_backup_path(root, runtime, run_id).resolve()
    try:
        backup_path = Path(result["path"]).resolve()
        manifest_path = Path(result["manifest_path"]).resolve()
    except (KeyError, TypeError, OSError) as error:
        raise BackupVerificationError("backup evidence is incomplete") from error
    if backup_path != expected_path:
        raise BackupVerificationError("backup path does not match the run")
    if manifest_path != backup_path / "manifest.json":
        raise BackupVerificationError("backup manifest path is invalid")
    if result.get("status") != "complete" or not manifest_path.is_file():
        raise BackupVerificationError("backup is not complete")
    if _manifest_digest(manifest_path) != result.get("manifest_sha256"):
        raise BackupVerificationError("backup manifest checksum does not match")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BackupVerificationError("backup manifest is unreadable") from error
    expected_identity = {
        "role": runtime.destination_role,
        "database": runtime.destination_database_name,
        "endpoint_fingerprint": runtime.destination_endpoint_fingerprint,
    }
    if (
        manifest.get("schema_version") != 1
        or manifest.get("extended_json_mode") != "canonical"
        or manifest.get("run_id") != run_id
        or manifest.get("status") != "complete"
        or manifest.get("device") != runtime.device
        or manifest.get("destination") != expected_identity
    ):
        raise BackupVerificationError("backup identity does not match the run")

    entries = manifest.get("collections")
    if not isinstance(entries, list):
        raise BackupVerificationError("backup collection evidence is invalid")
    names = set()
    document_count = 0
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise BackupVerificationError("backup collection entry is invalid")
        name = entry["name"]
        filename = f"{encode_collection_name(name)}.jsonl"
        if name in names or entry.get("filename") != filename:
            raise BackupVerificationError("backup collection identity is invalid")
        names.add(name)
        payload_path = (backup_path / filename).resolve()
        if payload_path.parent != backup_path or not payload_path.is_file():
            raise BackupVerificationError("backup collection payload is missing")
        details = _payload_details(payload_path)
        if any(entry.get(key) != value for key, value in details.items()):
            raise BackupVerificationError(
                "backup collection checksum or count does not match"
            )
        document_count += details["documents"]

    collection_count = len(entries)
    if (
        manifest.get("collection_count") != collection_count
        or manifest.get("document_count") != document_count
        or result.get("collection_count") != collection_count
        or result.get("document_count") != document_count
        or result.get("collections") != entries
    ):
        raise BackupVerificationError("backup aggregate counts do not match")
    return {
        "status": "complete",
        "collection_count": collection_count,
        "document_count": document_count,
        "manifest_sha256": result["manifest_sha256"],
    }


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
                "endpoint_fingerprint": (
                    runtime.destination_endpoint_fingerprint
                ),
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
                "endpoint_fingerprint": (
                    runtime.destination_endpoint_fingerprint
                ),
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
