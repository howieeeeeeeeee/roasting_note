#!/usr/bin/env python3
"""Generate docs/issues/README.md from ticket frontmatter.

The parser intentionally supports only the small YAML subset used by issue
tickets, so this script has no dependency beyond the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = ROOT / "docs" / "issues"
README = ISSUES_DIR / "README.md"
EXCLUDED = {"README.md", "TEMPLATE.md"}

STATUS_ORDER = ["pending", "in_progress", "resolved", "wont_fix"]
TYPE_LABELS = {
    "bug": "[BUG]",
    "feature": "[FEATURE]",
    "improvement": "[IMPROVEMENT]",
    "refactor": "[REFACTOR]",
    "todo": "[TODO]",
}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Ticket:
    path: Path
    metadata: dict[str, str | list[str]]

    @property
    def rel_link(self) -> str:
        return f"./{self.path.name}"

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
        return str(self.metadata.get("status", "pending")).lower()

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


def parse_frontmatter(path: Path) -> dict[str, str | list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} is missing frontmatter")

    metadata: dict[str, str | list[str]] = {}
    current_list_key: str | None = None

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return metadata

        if current_list_key and stripped.startswith("- "):
            value = stripped[2:].strip()
            cast_list = metadata.setdefault(current_list_key, [])
            if isinstance(cast_list, list):
                cast_list.append(value)
            continue

        current_list_key = None
        if ":" not in line:
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value == "":
            metadata[key] = ""
            current_list_key = key
        else:
            metadata[key] = value.strip('"').strip("'")

    raise ValueError(f"{path} frontmatter is not closed")


def load_tickets() -> list[Ticket]:
    tickets: list[Ticket] = []
    for path in sorted(ISSUES_DIR.glob("*.md")):
        if path.name in EXCLUDED:
            continue
        tickets.append(Ticket(path=path, metadata=parse_frontmatter(path)))
    return tickets


def sort_key(ticket: Ticket) -> tuple[int, int, str, str]:
    status_rank = STATUS_ORDER.index(ticket.status) if ticket.status in STATUS_ORDER else len(STATUS_ORDER)
    priority_rank = PRIORITY_ORDER.get(ticket.priority, 99)
    return (status_rank, priority_rank, ticket.created, ticket.id)


def status_heading(status: str) -> str:
    return {
        "pending": "Pending",
        "in_progress": "In Progress",
        "resolved": "Resolved",
        "wont_fix": "Won't Fix",
    }.get(status, status.replace("_", " ").title())


def render_table(tickets: list[Ticket], include_resolved: bool = False) -> list[str]:
    if not tickets:
        return ["No tickets."]

    lines = [
        "| ID | Type | Priority | Area | Title | Created | Resolved |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ticket in tickets:
        type_label = TYPE_LABELS.get(ticket.type, f"[{ticket.type.upper()}]")
        resolved = ticket.resolved if include_resolved else "-"
        lines.append(
            "| "
            f"{ticket.id} | "
            f"{type_label} | "
            f"{ticket.priority.title()} | "
            f"{ticket.area} | "
            f"[{ticket.title}]({ticket.rel_link}) | "
            f"{ticket.created or '-'} | "
            f"{resolved or '-'} |"
        )
    return lines


def render_readme(tickets: list[Ticket]) -> str:
    lines = [
        "# Issues",
        "",
        "Tracking for bugs, features, improvements, refactors, and todos.",
        "",
        "> This file is generated from ticket frontmatter. To update it, edit ticket metadata and run `uv run python scripts/generate_issues_index.py`.",
        "",
        "## Ticket Metadata",
        "",
        "Tickets live in `docs/issues/` as Markdown files with YAML frontmatter.",
        "Filenames are stable and do not need to change when status changes; use the `status` field instead.",
        "",
        "| Field | Values / Format | Notes |",
        "| --- | --- | --- |",
        "| `id` | `RN-0001` | Stable ticket identifier. Increment for new tickets. |",
        "| `title` | Text | Human-readable ticket title. |",
        "| `type` | `bug`, `feature`, `improvement`, `refactor`, `todo` | Work category. |",
        "| `status` | `pending`, `in_progress`, `resolved`, `wont_fix` | Drives this index. |",
        "| `priority` | `high`, `medium`, `low` | Used for sorting within status. |",
        "| `created` | `YYYY-MM-DD` | Creation date. |",
        "| `resolved` | `YYYY-MM-DD` or blank | Fill when resolved. |",
        "| `area` | Short slug | Example: `live-roasting`, `testing`, `docs`. |",
        "| `tags` | YAML list | Optional discovery labels. |",
        "",
        "Use `docs/issues/TEMPLATE.md` when creating a new ticket.",
        "",
        "## Current Tickets",
        "",
    ]

    visible_statuses = ["pending", "in_progress"]
    for status in visible_statuses:
        status_tickets = sorted([ticket for ticket in tickets if ticket.status == status], key=sort_key)
        lines.extend([f"### {status_heading(status)}", ""])
        lines.extend(render_table(status_tickets))
        lines.append("")

    resolved_tickets = sorted(
        [ticket for ticket in tickets if ticket.status == "resolved"],
        key=lambda ticket: (ticket.resolved or ticket.created, ticket.id),
        reverse=True,
    )
    lines.extend(["## Resolved Tickets", ""])
    lines.extend(render_table(resolved_tickets, include_resolved=True))
    lines.append("")

    other_statuses = sorted(
        {ticket.status for ticket in tickets} - set(visible_statuses) - {"resolved"}
    )
    for status in other_statuses:
        status_tickets = sorted([ticket for ticket in tickets if ticket.status == status], key=sort_key)
        lines.extend([f"## {status_heading(status)} Tickets", ""])
        lines.extend(render_table(status_tickets, include_resolved=True))
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    tickets = load_tickets()
    README.write_text(render_readme(tickets), encoding="utf-8")
    print(f"Generated {README.relative_to(ROOT)} from {len(tickets)} tickets")


if __name__ == "__main__":
    main()
