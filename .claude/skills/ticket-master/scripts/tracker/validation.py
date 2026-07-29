"""Tracker metadata, dependency, and canonical-path validation."""

from __future__ import annotations

import re
from pathlib import Path

from .records import (
    COMPLETED_TICKET_STATUSES,
    DECISION_STATUSES,
    TICKET_STATUSES,
    Decision,
    Record,
    Ticket,
    TrackerConfig,
    record_map,
)


def _validate_blocker_cycles(records: list[Record]) -> list[str]:
    by_id = {record.id: record for record in records}
    graph = {
        record.id: [
            item for item in record.blocked_by if item in by_id
        ]
        for record in records
    }
    errors = []
    visiting = []
    visited = set()

    def visit(record_id):
        if record_id in visited:
            return
        if record_id in visiting:
            start = visiting.index(record_id)
            errors.append(
                "blocker cycle: "
                + " -> ".join(visiting[start:] + [record_id])
            )
            return
        visiting.append(record_id)
        for blocker_id in graph.get(record_id, []):
            visit(blocker_id)
        visiting.pop()
        visited.add(record_id)

    for record_id in graph:
        visit(record_id)
    return errors


def _valid_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def validate_metadata(tickets, decisions, config: TrackerConfig) -> None:
    errors = []
    records = [*tickets, *decisions]
    ids = [record.id for record in records]
    duplicates = sorted(
        {record_id for record_id in ids if ids.count(record_id) > 1}
    )
    if duplicates:
        errors.append(f"duplicate ids: {', '.join(duplicates)}")
    by_id = record_map(tickets, decisions)

    for ticket in tickets:
        ticket_pattern = (
            rf"{re.escape(config.ticket_prefix)}-\d{{4}}(?:-\d{{2}})?"
        )
        child_pattern = rf"{re.escape(config.ticket_prefix)}-\d{{4}}-\d{{2}}"
        is_child_id = bool(re.fullmatch(child_pattern, ticket.id))
        if not re.fullmatch(ticket_pattern, ticket.id):
            errors.append(f"{ticket.path}: invalid ticket id {ticket.id!r}")
        if ticket.type not in config.ticket_types:
            errors.append(f"{ticket.id}: invalid ticket type {ticket.type!r}")
        if ticket.status not in TICKET_STATUSES:
            errors.append(f"{ticket.id}: invalid ticket status {ticket.status!r}")
        if ticket.priority not in config.priorities:
            errors.append(f"{ticket.id}: invalid priority {ticket.priority!r}")
        if not ticket.title or not ticket.created or not ticket.area:
            errors.append(f"{ticket.id}: title, created, and area are required")
        if ticket.created and not _valid_date(ticket.created):
            errors.append(f"{ticket.id}: invalid created date {ticket.created!r}")
        if ticket.resolved and not _valid_date(ticket.resolved):
            errors.append(f"{ticket.id}: invalid resolved date {ticket.resolved!r}")
        if "parent" not in ticket.metadata:
            errors.append(f"{ticket.id}: parent field is required")
        if "decisions" not in ticket.metadata or "blocked_by" not in ticket.metadata:
            errors.append(
                f"{ticket.id}: decisions and blocked_by fields are required"
            )
        if len(ticket.decisions) != len(set(ticket.decisions)):
            errors.append(f"{ticket.id}: duplicate decision ids")
        if len(ticket.blocked_by) != len(set(ticket.blocked_by)):
            errors.append(f"{ticket.id}: duplicate blocker ids")
        if ticket.type == "epic" and (ticket.parent or is_child_id):
            errors.append(
                f"{ticket.id}: an epic must use a top-level id and no parent"
            )
        if is_child_id and not ticket.parent:
            errors.append(f"{ticket.id}: child id requires a parent epic")
        if ticket.parent:
            parent = by_id.get(ticket.parent)
            if not isinstance(parent, Ticket) or parent.type != "epic":
                errors.append(
                    f"{ticket.id}: unknown or non-epic parent {ticket.parent}"
                )
            if not ticket.id.startswith(f"{ticket.parent}-"):
                errors.append(
                    f"{ticket.id}: child id must extend parent {ticket.parent}"
                )
        for decision_id in ticket.decisions:
            if not isinstance(by_id.get(decision_id), Decision):
                errors.append(f"{ticket.id}: unknown decision {decision_id}")
        for blocker_id in ticket.blocked_by:
            blocker = by_id.get(blocker_id)
            if blocker_id == ticket.id:
                errors.append(f"{ticket.id}: ticket cannot block itself")
            elif blocker is None:
                errors.append(f"{ticket.id}: unknown blocker {blocker_id}")
            elif isinstance(blocker, Decision) and blocker.status != "pending":
                errors.append(
                    f"{ticket.id}: finalized decision {blocker_id} is still a blocker"
                )
            elif (
                isinstance(blocker, Decision)
                and blocker_id not in ticket.decisions
            ):
                errors.append(
                    f"{ticket.id}: decision blocker {blocker_id} "
                    "must also appear in decisions"
                )
            elif (
                isinstance(blocker, Ticket)
                and blocker.status in COMPLETED_TICKET_STATUSES
            ):
                errors.append(
                    f"{ticket.id}: completed ticket {blocker_id} is still a blocker"
                )
        if ticket.status == "blocked" and not ticket.blocked_by:
            errors.append(f"{ticket.id}: blocked status requires blocked_by")
        if ticket.status != "blocked" and ticket.blocked_by:
            errors.append(f"{ticket.id}: blocked_by requires blocked status")
        if ticket.status in COMPLETED_TICKET_STATUSES and not ticket.resolved:
            errors.append(f"{ticket.id}: completed status requires resolved date")
        if ticket.status not in COMPLETED_TICKET_STATUSES and ticket.resolved:
            errors.append(f"{ticket.id}: active ticket must not have resolved date")

    for decision in decisions:
        pattern = rf"{re.escape(config.decision_prefix)}-\d{{4}}"
        if not re.fullmatch(pattern, decision.id):
            errors.append(f"{decision.path}: invalid decision id {decision.id!r}")
        if decision.status not in DECISION_STATUSES:
            errors.append(
                f"{decision.id}: invalid decision status {decision.status!r}"
            )
        if not decision.title or not decision.created or not decision.area:
            errors.append(f"{decision.id}: title, created, and area are required")
        if decision.created and not _valid_date(decision.created):
            errors.append(
                f"{decision.id}: invalid created date {decision.created!r}"
            )
        if decision.finalized and not _valid_date(decision.finalized):
            errors.append(
                f"{decision.id}: invalid finalized date {decision.finalized!r}"
            )
        if "blocked_by" not in decision.metadata:
            errors.append(f"{decision.id}: blocked_by field is required")
        if len(decision.blocked_by) != len(set(decision.blocked_by)):
            errors.append(f"{decision.id}: duplicate blocker ids")
        for blocker_id in decision.blocked_by:
            blocker = by_id.get(blocker_id)
            if blocker_id == decision.id:
                errors.append(f"{decision.id}: decision cannot block itself")
            elif blocker is None:
                errors.append(f"{decision.id}: unknown blocker {blocker_id}")
            elif isinstance(blocker, Decision) and blocker.status != "pending":
                errors.append(
                    f"{decision.id}: finalized decision {blocker_id} is still a blocker"
                )
            elif (
                isinstance(blocker, Ticket)
                and blocker.status in COMPLETED_TICKET_STATUSES
            ):
                errors.append(
                    f"{decision.id}: completed ticket {blocker_id} is still a blocker"
                )
        if decision.status == "pending" and (
            decision.finalized or decision.outcome
        ):
            errors.append(
                f"{decision.id}: pending decisions cannot have finalized/outcome"
            )
        if decision.status == "pending" and not any(
            decision.id in ticket.blocked_by for ticket in tickets
        ):
            errors.append(
                f"{decision.id}: a pending human decision must block at least one ticket"
            )
        if decision.status == "finalized" and (
            not decision.finalized or not decision.outcome
        ):
            errors.append(
                f"{decision.id}: finalized decisions require finalized and outcome"
            )
        if decision.status == "finalized" and decision.blocked_by:
            errors.append(
                f"{decision.id}: finalized decisions cannot retain blockers"
            )
    errors.extend(_validate_blocker_cycles(records))
    if errors:
        raise ValueError(
            "Invalid issue tracker metadata:\n- " + "\n- ".join(errors)
        )


def desired_paths(tickets, decisions, issues_dir: Path) -> dict[str, Path]:
    epics = {ticket.id: ticket for ticket in tickets if ticket.type == "epic"}
    paths = {}
    for ticket in tickets:
        status_dir = issues_dir / ticket.status
        if ticket.parent:
            paths[ticket.id] = (
                status_dir / epics[ticket.parent].path.stem / ticket.path.name
            )
        else:
            paths[ticket.id] = status_dir / ticket.path.name
    for decision in decisions:
        paths[decision.id] = (
            issues_dir / f"decision-{decision.status}" / decision.path.name
        )
    return paths


def validate_paths(tickets, decisions, issues_dir: Path) -> None:
    expected = desired_paths(tickets, decisions, issues_dir)
    errors = [
        f"{record.id}: expected {expected[record.id]}, found {record.path}"
        for record in [*tickets, *decisions]
        if record.path.resolve() != expected[record.id].resolve()
    ]
    if errors:
        raise ValueError(
            "Invalid issue tracker filing:\n- " + "\n- ".join(errors)
        )
