"""Append-only, sanitized audit records for database mirror operations."""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from roastlogger.services.database_sync_plan import planned_audit_path


def utc_text(value=None) -> str:
    current = value or datetime.now(timezone.utc)
    return current.isoformat().replace("+00:00", "Z")


def git_provenance(root: Path) -> dict:
    def read(*args):
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=root,
                capture_output=True,
                check=False,
                text=True,
            )
        except OSError:
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    status = read("status", "--porcelain")
    return {
        "commit": read("rev-parse", "HEAD") or "unavailable",
        "branch": read("branch", "--show-current") or "detached-or-unavailable",
        "dirty": status is None or bool(status),
    }


def _atomic_append_only_json(path: Path, record: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError("audit record already exists")
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    payload = json.dumps(record, indent=2, sort_keys=True) + "\n"
    try:
        with temporary.open("x", encoding="utf-8") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def write_applied_audit(root: Path, runtime, run_id: str, record: dict) -> Path:
    path = planned_audit_path(root, runtime, run_id)
    return _atomic_append_only_json(path, record)


def write_ui_intent_audit(
    root: Path,
    *,
    run_id: str,
    device: str,
    direction: str,
    record: dict,
) -> Path:
    timestamp = run_id.split("-", 1)[0]
    path = (
        root
        / "docs"
        / "audit_history"
        / "database_mirrors"
        / timestamp[:4]
        / timestamp[4:6]
        / f"{timestamp}__{device}__{direction}__{run_id}__preflight.json"
    )
    return _atomic_append_only_json(path, record)


def write_recovery_audit(backup_path: Path, record: dict) -> Path:
    backup_path.mkdir(parents=True, exist_ok=True)
    return _atomic_append_only_json(
        backup_path / "audit-recovery.json",
        record,
    )
