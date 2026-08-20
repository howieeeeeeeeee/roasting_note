"""Artifact-root-only fake executor for the guarded Settings E2E flow."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from roastlogger.services.database_backup import encode_collection_name
from roastlogger.services.database_sync_plan import (
    planned_audit_path,
    planned_backup_path,
)


def _utc_text():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class E2ESyncExecutor:
    """Return deterministic results without constructing or using MongoDB."""

    def __init__(self, artifact_root):
        self.artifact_root = Path(artifact_root).resolve()

    def _require_artifact_root(self, root):
        root = Path(root).resolve()
        if root != self.artifact_root:
            raise RuntimeError("E2E sync fake refused a non-artifact root")
        return root

    def _event(self, event):
        path = self.artifact_root / "sync-fake-events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as output:
            output.write(
                json.dumps(
                    {
                        "event": event,
                        "database_access": False,
                        "timestamp": _utc_text(),
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    def preflight(
        self,
        runtime,
        _source_client,
        _destination_client,
        root,
        *,
        run_id,
    ):
        root = self._require_artifact_root(root)
        self._event("preflight")
        return {
            "schema_version": 1,
            "run_id": run_id,
            "device": runtime.device,
            "direction": runtime.direction,
            "source": runtime.source_descriptor,
            "destination": runtime.destination_descriptor,
            "requested_collections": ["beans", "roasts"],
            "resolved_collections": ["beans", "roasts"],
            "batch_size": runtime.batch_size,
            "source_counts": {"beans": 2, "roasts": 1},
            "destination_counts": {"beans": 1, "roasts": 1},
            "backup": {
                "scope": "complete_destination_database",
                "collections": ["beans", "roasts", "e2e_metadata"],
                "counts": {"beans": 1, "roasts": 1, "e2e_metadata": 1},
                "path": str(planned_backup_path(root, runtime, run_id)),
            },
            "audit_path": str(planned_audit_path(root, runtime, run_id)),
            "cli_command": (
                "E2E simulation only; the guarded CLI is not invoked"
            ),
        }

    def backup(self, runtime, _destination_client, root, run_id):
        root = self._require_artifact_root(root)
        backup_path = planned_backup_path(root, runtime, run_id).resolve()
        if not backup_path.is_relative_to(self.artifact_root):
            raise RuntimeError("E2E sync fake refused a production backup path")
        backup_path.mkdir(parents=True, exist_ok=False)
        entries = []
        for name in ("beans", "roasts", "e2e_metadata"):
            filename = f"{encode_collection_name(name)}.jsonl"
            payload = json.dumps(
                {"e2e_fake": True, "collection": name},
                sort_keys=True,
            ).encode("utf-8") + b"\n"
            payload_path = backup_path / filename
            payload_path.write_bytes(payload)
            entries.append(
                {
                    "name": name,
                    "filename": filename,
                    "documents": 1,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        manifest = {
            "schema_version": 1,
            "extended_json_mode": "canonical",
            "run_id": run_id,
            "reason": "e2e_fake_guarded_database_sync_backup",
            "destination": {
                "role": runtime.destination_role,
                "database": runtime.destination_database_name,
                "endpoint_fingerprint": (
                    runtime.destination_endpoint_fingerprint
                ),
            },
            "device": runtime.device,
            "started_at": _utc_text(),
            "completed_at": _utc_text(),
            "status": "complete",
            "collections": entries,
            "collection_count": len(entries),
            "document_count": len(entries),
        }
        manifest_path = backup_path / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self._event("backup")
        return {
            "path": str(backup_path),
            "manifest_path": str(manifest_path),
            "manifest_sha256": hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest(),
            "status": "complete",
            "collection_count": len(entries),
            "document_count": len(entries),
            "collections": entries,
        }

    def synchronize(self, _runtime, _source_client, _destination_client):
        self._event("synchronize")
        collections = {
            "beans": {
                "added": 1,
                "updated": 1,
                "skipped": 0,
                "conflicts": 0,
                "post_run_count": 3,
            },
            "roasts": {
                "added": 1,
                "updated": 0,
                "skipped": 1,
                "conflicts": 0,
                "post_run_count": 2,
            },
        }
        return {
            "collections": collections,
            "aggregate": {
                "added": 2,
                "updated": 1,
                "skipped": 1,
                "conflicts": 0,
            },
            "verified": True,
        }
