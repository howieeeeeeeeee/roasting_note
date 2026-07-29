#!/usr/bin/env python3
"""Validate, file, and render RoastLogger issue-tracker records.

Tickets are filed by status. Child tickets sit in an epic-named folder within
their own status directory. Human decisions use separate pending/finalized
directories. Generated Markdown pages and the offline dashboard are derived
from frontmatter and ticket bodies.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Union

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib

from render_dashboard import render_dashboard


SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT = SKILL_ROOT.parents[2]
ISSUES_DIR = ROOT / "docs" / "issues"
CONFIG_NAME = "tracker.toml"

TICKET_STATUSES = ("in_progress", "blocked", "pending", "resolved", "wont_fix")
DECISION_STATUSES = ("pending", "finalized")
COMPLETED_TICKET_STATUSES = ("resolved", "wont_fix")
ACTIVE_TICKET_STATUSES = ("pending", "in_progress", "blocked")
STATUS_ALIASES = {"in-progress": "in_progress", "done": "resolved"}
STATUS_ORDER = {status: rank for rank, status in enumerate(TICKET_STATUSES)}

OVERVIEW_NAMES = {
    "in_progress": "in-progress.md",
    "blocked": "blocked.md",
    "pending": "pending.md",
    "done": "done.md",
    "decisions": "human-decisions.md",
}
HTML_OVERVIEW_NAME = "overview.html"
GENERATED_NAMES = {"README.md", *OVERVIEW_NAMES.values()}
TEMPLATE_NAMES = {"TEMPLATE.md", "TICKET.md", "HUMAN_DECISION.md"}

GEN_NOTE = (
    "> Generated from frontmatter by "
    "`.claude/skills/ticket-master/scripts/generate_issues_index.py`. "
    "Do not edit by hand."
)
RELATED_START = "<!-- BEGIN GENERATED RELATED WORK -->"
RELATED_END = "<!-- END GENERATED RELATED WORK -->"

Metadata = dict[str, Union[str, list[str]]]


@dataclass(frozen=True)
class TrackerConfig:
    project_name: str
    description: str
    ticket_prefix: str
    decision_prefix: str
    ticket_types: tuple[str, ...]
    priorities: tuple[str, ...]

    @property
    def priority_order(self) -> dict[str, int]:
        return {priority: rank for rank, priority in enumerate(self.priorities)}


def load_config(issues_dir: Path = ISSUES_DIR) -> TrackerConfig:
    path = issues_dir / CONFIG_NAME
    if not path.exists():
        raise ValueError(f"{path} is required")
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    project = raw.get("project", {})
    scalar_values = {
        "project_name": str(project.get("name", "")).strip(),
        "description": str(project.get("description", "")).strip(),
        "ticket_prefix": str(project.get("ticket_prefix", "")).strip(),
        "decision_prefix": str(project.get("decision_prefix", "")).strip(),
    }
    missing = [key for key, value in scalar_values.items() if not value]
    if missing:
        raise ValueError(f"{path}: missing project fields: {', '.join(missing)}")
    for key in ("ticket_prefix", "decision_prefix"):
        if not re.fullmatch(r"[A-Z][A-Z0-9]*", scalar_values[key]):
            raise ValueError(f"{path}: {key} must contain uppercase letters and digits")

    ticket_types = tuple(
        str(item).strip().lower() for item in project.get("ticket_types", [])
    )
    priorities = tuple(
        str(item).strip().lower() for item in project.get("priorities", [])
    )
    if not ticket_types or "epic" not in ticket_types:
        raise ValueError(f"{path}: ticket_types must include epic")
    if not priorities:
        raise ValueError(f"{path}: priorities must not be empty")
    if len(ticket_types) != len(set(ticket_types)):
        raise ValueError(f"{path}: ticket_types contains duplicates")
    if len(priorities) != len(set(priorities)):
        raise ValueError(f"{path}: priorities contains duplicates")
    return TrackerConfig(
        **scalar_values,
        ticket_types=ticket_types,
        priorities=priorities,
    )


def metadata_list(metadata: Metadata, key: str) -> list[str]:
    value = metadata.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)] if value else []


@dataclass
class Ticket:
    path: Path
    metadata: Metadata

    @property
    def id(self) -> str:
        return str(self.metadata.get("id", ""))

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", self.path.stem))

    @property
    def type(self) -> str:
        return str(self.metadata.get("type", "todo")).lower()

    @property
    def status(self) -> str:
        raw = str(self.metadata.get("status", "pending")).lower()
        return STATUS_ALIASES.get(raw, raw)

    @property
    def priority(self) -> str:
        return str(self.metadata.get("priority", "medium")).lower()

    @property
    def area(self) -> str:
        return str(self.metadata.get("area", "general"))

    @property
    def created(self) -> str:
        return str(self.metadata.get("created", ""))

    @property
    def resolved(self) -> str:
        return str(self.metadata.get("resolved", "") or "")

    @property
    def parent(self) -> str:
        return str(self.metadata.get("parent", "") or "")

    @property
    def decisions(self) -> list[str]:
        return metadata_list(self.metadata, "decisions")

    @property
    def blocked_by(self) -> list[str]:
        return metadata_list(self.metadata, "blocked_by")

    @property
    def tags(self) -> list[str]:
        return metadata_list(self.metadata, "tags")


@dataclass
class Decision:
    path: Path
    metadata: Metadata

    @property
    def id(self) -> str:
        return str(self.metadata.get("id", ""))

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", self.path.stem))

    @property
    def status(self) -> str:
        return str(self.metadata.get("status", "pending")).lower()

    @property
    def created(self) -> str:
        return str(self.metadata.get("created", ""))

    @property
    def finalized(self) -> str:
        return str(self.metadata.get("finalized", "") or "")

    @property
    def outcome(self) -> str:
        return str(self.metadata.get("outcome", "") or "")

    @property
    def area(self) -> str:
        return str(self.metadata.get("area", "general"))

    @property
    def decided_by(self) -> str:
        return str(self.metadata.get("decided_by", "") or "")

    @property
    def blocked_by(self) -> list[str]:
        return metadata_list(self.metadata, "blocked_by")

    @property
    def tags(self) -> list[str]:
        return metadata_list(self.metadata, "tags")


Record = Union[Ticket, Decision]


def _parse_inline_list(value: str) -> list[str] | None:
    if not (value.startswith("[") and value.endswith("]")):
        return None
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",")]


def parse_frontmatter(path: Path) -> Metadata:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} is missing frontmatter")

    metadata: Metadata = {}
    current_list_key: str | None = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return metadata
        if current_list_key and stripped.startswith("- "):
            value = stripped[2:].strip().strip('"').strip("'")
            current = metadata.setdefault(current_list_key, [])
            if isinstance(current, list):
                current.append(value)
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        inline_list = _parse_inline_list(value)
        if inline_list is not None:
            metadata[key] = inline_list
        elif value == "":
            metadata[key] = ""
            current_list_key = key
        else:
            metadata[key] = value.strip('"').strip("'")
    raise ValueError(f"{path} frontmatter is not closed")


def _is_tracker_record(path: Path, issues_dir: Path) -> bool:
    if path.name in GENERATED_NAMES or path.name in TEMPLATE_NAMES:
        return False
    try:
        relative = path.relative_to(issues_dir)
    except ValueError:
        return False
    return "templates" not in relative.parts


def load_records(
    issues_dir: Path = ISSUES_DIR,
) -> tuple[list[Ticket], list[Decision]]:
    tickets: list[Ticket] = []
    decisions: list[Decision] = []
    for path in sorted(issues_dir.rglob("*.md")):
        if not _is_tracker_record(path, issues_dir):
            continue
        metadata = parse_frontmatter(path)
        if str(metadata.get("type", "")).lower() == "human-decision":
            decisions.append(Decision(path, metadata))
        else:
            tickets.append(Ticket(path, metadata))
    return tickets, decisions


def record_map(
    tickets: list[Ticket], decisions: list[Decision]
) -> dict[str, Record]:
    return {record.id: record for record in [*tickets, *decisions]}


def _validate_blocker_cycles(records: list[Record]) -> list[str]:
    by_id = {record.id: record for record in records}
    graph = {
        record.id: [item for item in record.blocked_by if item in by_id]
        for record in records
    }
    errors: list[str] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(record_id: str) -> None:
        if record_id in visited:
            return
        if record_id in visiting:
            start = visiting.index(record_id)
            errors.append("blocker cycle: " + " -> ".join(visiting[start:] + [record_id]))
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


def validate_metadata(
    tickets: list[Ticket],
    decisions: list[Decision],
    config: TrackerConfig,
) -> None:
    errors: list[str] = []
    records = [*tickets, *decisions]
    ids = [record.id for record in records]
    duplicate_ids = sorted(
        {record_id for record_id in ids if ids.count(record_id) > 1}
    )
    if duplicate_ids:
        errors.append(f"duplicate ids: {', '.join(duplicate_ids)}")
    by_id = record_map(tickets, decisions)

    for ticket in tickets:
        ticket_pattern = rf"{re.escape(config.ticket_prefix)}-\d{{4}}(?:-\d{{2}})?"
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
            errors.append(f"{ticket.id}: decisions and blocked_by fields are required")
        if len(ticket.decisions) != len(set(ticket.decisions)):
            errors.append(f"{ticket.id}: duplicate decision ids")
        if len(ticket.blocked_by) != len(set(ticket.blocked_by)):
            errors.append(f"{ticket.id}: duplicate blocker ids")

        if ticket.type == "epic" and (ticket.parent or is_child_id):
            errors.append(f"{ticket.id}: an epic must use a top-level id and no parent")
        if is_child_id and not ticket.parent:
            errors.append(f"{ticket.id}: child id requires a parent epic")
        if ticket.parent:
            parent = by_id.get(ticket.parent)
            if not isinstance(parent, Ticket) or parent.type != "epic":
                errors.append(f"{ticket.id}: unknown or non-epic parent {ticket.parent}")
            if not ticket.id.startswith(f"{ticket.parent}-"):
                errors.append(f"{ticket.id}: child id must extend parent {ticket.parent}")

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
            elif isinstance(blocker, Decision) and blocker_id not in ticket.decisions:
                errors.append(
                    f"{ticket.id}: decision blocker {blocker_id} must also appear in decisions"
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
        decision_pattern = rf"{re.escape(config.decision_prefix)}-\d{{4}}"
        if not re.fullmatch(decision_pattern, decision.id):
            errors.append(f"{decision.path}: invalid decision id {decision.id!r}")
        if decision.status not in DECISION_STATUSES:
            errors.append(f"{decision.id}: invalid decision status {decision.status!r}")
        if not decision.title or not decision.created or not decision.area:
            errors.append(f"{decision.id}: title, created, and area are required")
        if decision.created and not _valid_date(decision.created):
            errors.append(f"{decision.id}: invalid created date {decision.created!r}")
        if decision.finalized and not _valid_date(decision.finalized):
            errors.append(f"{decision.id}: invalid finalized date {decision.finalized!r}")
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
        if decision.status == "pending" and (decision.finalized or decision.outcome):
            errors.append(f"{decision.id}: pending decisions cannot have finalized/outcome")
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
            errors.append(f"{decision.id}: finalized decisions cannot retain blockers")

    errors.extend(_validate_blocker_cycles(records))
    if errors:
        raise ValueError("Invalid issue tracker metadata:\n- " + "\n- ".join(errors))


def desired_paths(
    tickets: list[Ticket],
    decisions: list[Decision],
    issues_dir: Path,
) -> dict[str, Path]:
    epics = {ticket.id: ticket for ticket in tickets if ticket.type == "epic"}
    paths: dict[str, Path] = {}
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


def validate_paths(
    tickets: list[Ticket],
    decisions: list[Decision],
    issues_dir: Path,
) -> None:
    expected = desired_paths(tickets, decisions, issues_dir)
    errors = [
        f"{record.id}: expected {expected[record.id]}, found {record.path}"
        for record in [*tickets, *decisions]
        if record.path.resolve() != expected[record.id].resolve()
    ]
    if errors:
        raise ValueError("Invalid issue tracker filing:\n- " + "\n- ".join(errors))


def _ensure_layout_dirs(issues_dir: Path) -> set[Path]:
    directories = {issues_dir / status for status in TICKET_STATUSES} | {
        issues_dir / f"decision-{status}" for status in DECISION_STATUSES
    } | {issues_dir / "templates"}
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def _remove_empty_legacy_dirs(issues_dir: Path, protected: set[Path]) -> None:
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


def file_records(
    tickets: list[Ticket],
    decisions: list[Decision],
    issues_dir: Path,
) -> int:
    destinations = desired_paths(tickets, decisions, issues_dir)
    records = [*tickets, *decisions]
    destination_ids: dict[Path, str] = {}
    for record in records:
        destination = destinations[record.id]
        previous = destination_ids.get(destination)
        if previous:
            raise ValueError(
                f"{previous} and {record.id} share destination {destination}"
            )
        destination_ids[destination] = record.id
        if destination.exists() and destination.resolve() != record.path.resolve():
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


def relative_link(target: Path, from_dir: Path) -> str:
    relative = Path(os.path.relpath(target, start=from_dir)).as_posix()
    return relative if relative.startswith(".") else f"./{relative}"


def linked_id(
    record_id: str,
    by_id: dict[str, Record],
    from_dir: Path,
) -> str:
    record = by_id.get(record_id)
    if record is None:
        return record_id
    return f"[{record_id}]({relative_link(record.path, from_dir)})"


def status_heading(status: str) -> str:
    return {
        "pending": "Pending",
        "in_progress": "In Progress",
        "blocked": "Blocked",
        "resolved": "Resolved",
        "wont_fix": "Won't Fix",
        "finalized": "Finalized",
    }.get(status, status.replace("_", " ").title())


def ticket_sort_key(
    ticket: Ticket,
    config: TrackerConfig,
) -> tuple[int, str, str]:
    return (
        config.priority_order.get(ticket.priority, 99),
        ticket.created,
        ticket.id,
    )


def completed_sort_key(ticket: Ticket) -> tuple[str, str]:
    return (ticket.resolved or ticket.created, ticket.id)


def render_ticket_table(
    tickets: list[Ticket],
    by_id: dict[str, Record],
    from_dir: Path,
    *,
    include_resolved: bool = False,
) -> list[str]:
    if not tickets:
        return ["No tickets."]
    lines = [
        "| ID | Type | Priority | Area | Title | Parent | Blocked by | Created | Resolved |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ticket in tickets:
        parent = linked_id(ticket.parent, by_id, from_dir) if ticket.parent else "-"
        blockers = ", ".join(
            linked_id(item, by_id, from_dir) for item in ticket.blocked_by
        ) or "-"
        resolved = ticket.resolved if include_resolved else "-"
        lines.append(
            "| "
            f"{ticket.id} | [{ticket.type.upper()}] | "
            f"{ticket.priority.title()} | {ticket.area} | "
            f"[{ticket.title}]({relative_link(ticket.path, from_dir)}) | "
            f"{parent} | {blockers} | {ticket.created or '-'} | {resolved or '-'} |"
        )
    return lines


def render_status_page(
    tickets: list[Ticket],
    decisions: list[Decision],
    status: str,
    config: TrackerConfig,
    issues_dir: Path,
) -> str:
    by_id = record_map(tickets, decisions)
    selected = sorted(
        [ticket for ticket in tickets if ticket.status == status],
        key=lambda ticket: ticket_sort_key(ticket, config),
    )
    lines = [f"# {status_heading(status)}", "", GEN_NOTE, ""]
    lines.extend(render_ticket_table(selected, by_id, issues_dir))
    lines.append("")
    return "\n".join(lines)


def render_done_page(
    tickets: list[Ticket],
    decisions: list[Decision],
    issues_dir: Path,
) -> str:
    by_id = record_map(tickets, decisions)
    lines = ["# Done", "", GEN_NOTE, ""]
    for status in COMPLETED_TICKET_STATUSES:
        selected = sorted(
            [ticket for ticket in tickets if ticket.status == status],
            key=completed_sort_key,
            reverse=True,
        )
        lines.extend([f"## {status_heading(status)}", ""])
        lines.extend(
            render_ticket_table(
                selected,
                by_id,
                issues_dir,
                include_resolved=True,
            )
        )
        lines.append("")
    return "\n".join(lines)


def related_tickets(
    decision: Decision,
    tickets: list[Ticket],
) -> list[Ticket]:
    return sorted(
        [ticket for ticket in tickets if decision.id in ticket.decisions],
        key=lambda ticket: (STATUS_ORDER.get(ticket.status, 99), ticket.id),
    )


def render_decision_ticket_table(
    decision: Decision,
    tickets: list[Ticket],
    by_id: dict[str, Record],
    from_dir: Path,
) -> list[str]:
    related = related_tickets(decision, tickets)
    if not related:
        return ["No related tickets."]
    lines = [
        "| Ticket | Parent epic | Current status | Blocked by |",
        "| --- | --- | --- | --- |",
    ]
    for ticket in related:
        parent = linked_id(ticket.parent, by_id, from_dir) if ticket.parent else "-"
        blockers = ", ".join(
            linked_id(item, by_id, from_dir) for item in ticket.blocked_by
        ) or "-"
        lines.append(
            f"| [{ticket.id}: {ticket.title}]"
            f"({relative_link(ticket.path, from_dir)}) | "
            f"{parent} | {status_heading(ticket.status)} | {blockers} |"
        )
    return lines


def render_decisions_page(
    tickets: list[Ticket],
    decisions: list[Decision],
    issues_dir: Path,
) -> str:
    by_id = record_map(tickets, decisions)
    lines = ["# Human Decisions", "", GEN_NOTE, ""]
    if not decisions:
        return "\n".join([*lines, "No human decisions.", ""])
    for decision in sorted(
        decisions,
        key=lambda item: (item.created, item.id),
        reverse=True,
    ):
        readiness = (
            "Finalized"
            if decision.status == "finalized"
            else "Ready" if not decision.blocked_by else "Waiting"
        )
        lines.extend(
            [
                f"### {decision.id}",
                "",
                f"**[{decision.title}]"
                f"({relative_link(decision.path, issues_dir)})**",
                "",
                f"- Status: **{status_heading(decision.status)}**",
                f"- Readiness: **{readiness}**",
                "- Blocked by: "
                + (
                    ", ".join(
                        linked_id(item, by_id, issues_dir)
                        for item in decision.blocked_by
                    )
                    or "-"
                ),
                f"- Created: {decision.created or '-'}",
                f"- Finalized: {decision.finalized or '-'}",
                f"- Outcome: {decision.outcome or 'Pending'}",
                "",
            ]
        )
        lines.extend(
            render_decision_ticket_table(decision, tickets, by_id, issues_dir)
        )
        lines.append("")
    return "\n".join(lines)


def updated_decision_text(
    decision: Decision,
    tickets: list[Ticket],
    decisions: list[Decision],
) -> str:
    by_id = record_map(tickets, decisions)
    text = decision.path.read_text(encoding="utf-8")
    if RELATED_START not in text or RELATED_END not in text:
        raise ValueError(
            f"{decision.id}: decision document is missing generated-work markers"
        )
    before, remainder = text.split(RELATED_START, 1)
    _, after = remainder.split(RELATED_END, 1)
    table = "\n".join(
        render_decision_ticket_table(
            decision,
            tickets,
            by_id,
            decision.path.parent,
        )
    )
    return f"{before}{RELATED_START}\n\n{table}\n\n{RELATED_END}{after}"


def refresh_decision_related_work(
    tickets: list[Ticket],
    decisions: list[Decision],
) -> None:
    for decision in decisions:
        decision.path.write_text(
            updated_decision_text(decision, tickets, decisions),
            encoding="utf-8",
        )


def _csv_code(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def render_readme(
    tickets: list[Ticket],
    decisions: list[Decision],
    config: TrackerConfig,
) -> str:
    counts = {
        status: sum(ticket.status == status for ticket in tickets)
        for status in TICKET_STATUSES
    }
    decision_counts = {
        status: sum(decision.status == status for decision in decisions)
        for status in DECISION_STATUSES
    }
    done_total = counts["resolved"] + counts["wont_fix"]
    return "\n".join(
        [
            "# Issues",
            "",
            f"Issue and human-decision tracker for {config.project_name}. "
            f"{config.description}",
            "",
            GEN_NOTE,
            "> Run `uv run python scripts/generate_issues_index.py` from the repository root after editing any record.",
            "",
            "## Status Overviews",
            "",
            "- [Visual Overview](./overview.html) — self-contained offline dashboard",
            f"- [In Progress](./in-progress.md) — {counts['in_progress']}",
            f"- [Blocked](./blocked.md) — {counts['blocked']}",
            f"- [Pending](./pending.md) — {counts['pending']}",
            f"- [Done](./done.md) — {done_total} "
            f"(resolved {counts['resolved']}, won't-fix {counts['wont_fix']})",
            f"- [Human Decisions](./human-decisions.md) — "
            f"{decision_counts['pending']} pending, "
            f"{decision_counts['finalized']} finalized",
            "",
            "## Folder Layout",
            "",
            "- File every epic and ticket by its own status under `pending/`, `in_progress/`, `blocked/`, `resolved/`, or `wont_fix/`.",
            "- File a child ticket in an epic-named folder within its own status directory.",
            "- File human decisions under `decision-pending/` or `decision-finalized/`.",
            "- Keep ticket and decision templates under `templates/`.",
            "- Treat ids as stable; status transitions change paths.",
            "",
            "## Ticket Metadata",
            "",
            "| Field | Values / Format | Notes |",
            "| --- | --- | --- |",
            f"| `id` | `{config.ticket_prefix}-0001` or "
            f"`{config.ticket_prefix}-0001-01` | Stable epic/ticket id. |",
            "| `title` | Text | Human-readable title. |",
            f"| `type` | {_csv_code(config.ticket_types)} | Epics group child tickets; other values categorize work. |",
            f"| `status` | {_csv_code(TICKET_STATUSES)} | Drives filing and overviews. |",
            f"| `priority` | {_csv_code(config.priorities)} | Sort order within a status. |",
            "| `created` / `resolved` | `YYYY-MM-DD` | Completed work requires a resolution date. |",
            f"| `parent` | `{config.ticket_prefix}-XXXX` or blank | Parent epic for child tickets. |",
            f"| `decisions` | List of `{config.decision_prefix}-XXXX` ids | Durable decision provenance. |",
            f"| `blocked_by` | List of unresolved `{config.decision_prefix}-XXXX` or `{config.ticket_prefix}-...` ids | Current blockers; nonempty exactly when status is blocked. |",
            "| `area` / `tags` | Slug / YAML list | Discovery metadata. |",
            "",
            "Use `docs/issues/templates/TICKET.md` for work and "
            "`docs/issues/templates/HUMAN_DECISION.md` for human choices.",
            "",
            "## Human-Decision Metadata",
            "",
            "| Field | Values / Format | Notes |",
            "| --- | --- | --- |",
            f"| `id` | `{config.decision_prefix}-XXXX` | Sequential human-decision id. |",
            "| `type` | `human-decision` | Separates decisions from implementation work. |",
            "| `status` | `pending`, `finalized` | Finalized requires an outcome and date. |",
            "| `outcome` | Allowed outcome key or blank | Exact recorded choice after finalization. |",
            "| `decided_by` | Name/role or blank | Optional provenance. |",
            "| `blocked_by` | Unfinished ticket or pending-decision ids | Empty means ready for review; nonempty means waiting for evidence. |",
            "",
            "## Block Logic",
            "",
            "A ticket is `blocked` exactly when `blocked_by` is nonempty. "
            "A pending decision is ready exactly when `blocked_by` is empty. "
            "Finalizing a decision or resolving a ticket removes only that id "
            "from downstream blockers. A blocked ticket becomes pending only "
            "after no blockers remain.",
            "",
            "## Documentation Gate",
            "",
            "Every new or refined ticket records exact documentation targets "
            "under `## Documentation Impact`. Before resolution, compare the "
            "implementation diff with `.claude/skills/ticket-master/"
            "DOCUMENTATION_WORKFLOW.md` and update every affected document in "
            "the same branch.",
            "",
        ]
    )


def generated_files(
    tickets: list[Ticket],
    decisions: list[Decision],
    config: TrackerConfig,
    issues_dir: Path,
) -> dict[Path, str]:
    outputs = {
        issues_dir / "README.md": render_readme(tickets, decisions, config),
        issues_dir / OVERVIEW_NAMES["done"]: render_done_page(
            tickets,
            decisions,
            issues_dir,
        ),
        issues_dir / OVERVIEW_NAMES["decisions"]: render_decisions_page(
            tickets,
            decisions,
            issues_dir,
        ),
        issues_dir / HTML_OVERVIEW_NAME: render_dashboard(
            config,
            tickets,
            decisions,
            issues_dir,
        ),
    }
    for status in ACTIVE_TICKET_STATUSES:
        outputs[issues_dir / OVERVIEW_NAMES[status]] = render_status_page(
            tickets,
            decisions,
            status,
            config,
            issues_dir,
        )
    return outputs


def check_generated(
    tickets: list[Ticket],
    decisions: list[Decision],
    config: TrackerConfig,
    issues_dir: Path,
) -> None:
    def display_path(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)

    stale: list[str] = []
    for decision in decisions:
        expected = updated_decision_text(decision, tickets, decisions)
        if decision.path.read_text(encoding="utf-8") != expected:
            stale.append(display_path(decision.path))
    for path, expected in generated_files(
        tickets,
        decisions,
        config,
        issues_dir,
    ).items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(display_path(path))
    if stale:
        raise ValueError(
            "Stale generated issue tracker files:\n- " + "\n- ".join(stale)
        )


def generate(
    issues_dir: Path = ISSUES_DIR,
    *,
    check: bool = False,
) -> tuple[int, int, int]:
    config = load_config(issues_dir)
    tickets, decisions = load_records(issues_dir)
    validate_metadata(tickets, decisions, config)
    if check:
        validate_paths(tickets, decisions, issues_dir)
        check_generated(tickets, decisions, config, issues_dir)
        return len(tickets), len(decisions), 0

    moved = file_records(tickets, decisions, issues_dir)
    tickets, decisions = load_records(issues_dir)
    validate_metadata(tickets, decisions, config)
    validate_paths(tickets, decisions, issues_dir)
    refresh_decision_related_work(tickets, decisions)

    tickets, decisions = load_records(issues_dir)
    for path, content in generated_files(
        tickets,
        decisions,
        config,
        issues_dir,
    ).items():
        path.write_text(content, encoding="utf-8")
    return len(tickets), len(decisions), moved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate canonical paths and fail when generated files are stale",
    )
    args = parser.parse_args()
    ticket_count, decision_count, moved = generate(check=args.check)
    verb = "Checked" if args.check else "Generated index from"
    filing = "" if args.check else f" ({moved} records filed by status)"
    print(
        f"{verb} {ticket_count} tickets and "
        f"{decision_count} decisions{filing}"
    )


if __name__ == "__main__":
    main()
