"""Tracker metadata, dependency, and canonical-path validation."""

from __future__ import annotations

import re
from pathlib import Path

from .records import (
    ACTIVE_TICKET_STATUSES,
    COMPLETED_TICKET_STATUSES,
    DECISION_STATUSES,
    TICKET_STATUSES,
    Decision,
    Record,
    Ticket,
    TrackerConfig,
    record_map,
)

TESTING_POLICY_VERSION = "v1"
TESTING_IMPACT_FIELDS = (
    "Change classification",
    "Automated tests to add or update",
    "Browser E2E scenarios to add or update",
    "Required commands",
    "Required browser evidence",
    "Not applicable reason",
)
UI_TEST_CLASSIFICATIONS = (
    "ui-visual",
    "ui-interaction",
    "cross-workflow",
    "release",
)
TESTING_ACCEPTANCE_TEXT = (
    "Testing Impact reviewed against the implementation diff; "
    "declared automated and browser coverage is complete."
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


def _markdown_section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        return None
    remainder = text[match.end() :]
    next_heading = re.search(r"^## ", remainder, flags=re.MULTILINE)
    return remainder[: next_heading.start()] if next_heading else remainder


def _testing_field(section: str, label: str) -> str | None:
    match = re.search(
        rf"^- {re.escape(label)}:\s*(.*?)\s*$",
        section,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _is_not_applicable(value: str | None) -> bool:
    normalized = (value or "").strip().lower().rstrip(".")
    return normalized in {"none", "n/a", "not applicable"}


def _is_placeholder(value: str | None) -> bool:
    normalized = (value or "").strip().lower().rstrip(".")
    return normalized in {"", "tbd", "todo", "placeholder"}


def _validate_testing_impact(ticket: Ticket) -> list[str]:
    errors = []
    policy = str(ticket.metadata.get("testing_policy", "") or "")
    if ticket.status in ACTIVE_TICKET_STATUSES and (
        policy != TESTING_POLICY_VERSION
    ):
        errors.append(
            f"{ticket.id}: active ticket requires "
            f"testing_policy: {TESTING_POLICY_VERSION}"
        )
    if policy and policy != TESTING_POLICY_VERSION:
        errors.append(f"{ticket.id}: unsupported testing_policy {policy!r}")
    if policy != TESTING_POLICY_VERSION:
        return errors

    text = ticket.path.read_text(encoding="utf-8")
    section = _markdown_section(text, "Testing Impact")
    if section is None:
        errors.append(f"{ticket.id}: testing policy requires Testing Impact")
        return errors

    values = {
        label: _testing_field(section, label)
        for label in TESTING_IMPACT_FIELDS
    }
    for label, value in values.items():
        if _is_placeholder(value):
            errors.append(
                f"{ticket.id}: Testing Impact field {label!r} is required"
            )

    checkbox = re.search(
        rf"^- \[([ xX])\] {re.escape(TESTING_ACCEPTANCE_TEXT)}$",
        text,
        flags=re.MULTILINE,
    )
    if not checkbox:
        errors.append(
            f"{ticket.id}: testing policy requires its acceptance checkbox"
        )
    elif (
        ticket.status in COMPLETED_TICKET_STATUSES
        and checkbox.group(1).lower() != "x"
    ):
        errors.append(
            f"{ticket.id}: completed ticket requires checked Testing Impact"
        )

    classification = (values["Change classification"] or "").lower()
    requires_browser = any(
        item in classification for item in UI_TEST_CLASSIFICATIONS
    )
    browser_scenarios = values["Browser E2E scenarios to add or update"]
    browser_evidence = values["Required browser evidence"]
    if requires_browser and (
        _is_not_applicable(browser_scenarios)
        or _is_not_applicable(browser_evidence)
    ):
        errors.append(
            f"{ticket.id}: UI testing classification requires browser "
            "scenarios and evidence"
        )

    coverage_fields = (
        values["Automated tests to add or update"],
        browser_scenarios,
        browser_evidence,
    )
    if any(_is_not_applicable(value) for value in coverage_fields) and (
        _is_not_applicable(values["Not applicable reason"])
        or _is_placeholder(values["Not applicable reason"])
    ):
        errors.append(
            f"{ticket.id}: omitted testing coverage requires a concrete "
            "Not applicable reason"
        )
    return errors


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
        errors.extend(_validate_testing_impact(ticket))
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
