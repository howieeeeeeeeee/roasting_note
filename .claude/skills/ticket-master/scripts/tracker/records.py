"""Tracker configuration, record models, and frontmatter parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Union

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


SKILL_ROOT = Path(__file__).resolve().parents[2]
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
        return {
            priority: rank
            for rank, priority in enumerate(self.priorities)
        }


def load_config(issues_dir: Path = ISSUES_DIR) -> TrackerConfig:
    path = issues_dir / CONFIG_NAME
    if not path.exists():
        raise ValueError(f"{path} is required")
    with path.open("rb") as handle:
        project = tomllib.load(handle).get("project", {})
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
            raise ValueError(
                f"{path}: {key} must contain uppercase letters and digits"
            )

    ticket_types = tuple(
        str(item).strip().lower()
        for item in project.get("ticket_types", [])
    )
    priorities = tuple(
        str(item).strip().lower()
        for item in project.get("priorities", [])
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
    return [
        item.strip().strip('"').strip("'")
        for item in inner.split(",")
    ]


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
    tickets: list[Ticket],
    decisions: list[Decision],
) -> dict[str, Record]:
    return {record.id: record for record in [*tickets, *decisions]}
