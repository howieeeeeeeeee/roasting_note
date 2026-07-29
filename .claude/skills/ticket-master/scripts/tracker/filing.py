"""Canonical tracker record filing."""

from __future__ import annotations

import shutil
from pathlib import Path

from .records import DECISION_STATUSES, TICKET_STATUSES
from .validation import desired_paths


def _ensure_layout_dirs(issues_dir: Path) -> set[Path]:
    directories = {issues_dir / status for status in TICKET_STATUSES} | {
        issues_dir / f"decision-{status}" for status in DECISION_STATUSES
    } | {issues_dir / "templates"}
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def _remove_empty_legacy_dirs(
    issues_dir: Path,
    protected: set[Path],
) -> None:
    directories = sorted(
        (path for path in issues_dir.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        if directory in protected:
            continue
        try:
            directory.rmdir()
        except OSError:
            pass


def file_records(tickets, decisions, issues_dir: Path) -> int:
    destinations = desired_paths(tickets, decisions, issues_dir)
    records = [*tickets, *decisions]
    destination_ids = {}
    for record in records:
        destination = destinations[record.id]
        previous = destination_ids.get(destination)
        if previous:
            raise ValueError(
                f"{previous} and {record.id} share destination {destination}"
            )
        destination_ids[destination] = record.id
        if (
            destination.exists()
            and destination.resolve() != record.path.resolve()
        ):
            raise FileExistsError(f"refusing to overwrite {destination}")

    moved = 0
    protected = _ensure_layout_dirs(issues_dir)
    for record in records:
        destination = destinations[record.id]
        if record.path.resolve() == destination.resolve():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(record.path), str(destination))
        moved += 1
    _remove_empty_legacy_dirs(issues_dir, protected)
    return moved
