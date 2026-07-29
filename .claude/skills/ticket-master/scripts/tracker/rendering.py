"""Markdown and decision-related-work rendering."""

from __future__ import annotations

import os
from pathlib import Path

from .records import (
    COMPLETED_TICKET_STATUSES,
    DECISION_STATUSES,
    GEN_NOTE,
    OVERVIEW_NAMES,
    RELATED_END,
    RELATED_START,
    STATUS_ORDER,
    TICKET_STATUSES,
    Decision,
    Record,
    Ticket,
    TrackerConfig,
    record_map,
)


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
        parent = (
            linked_id(ticket.parent, by_id, from_dir)
            if ticket.parent
            else "-"
        )
        blockers = ", ".join(
            linked_id(item, by_id, from_dir)
            for item in ticket.blocked_by
        ) or "-"
        resolved = ticket.resolved if include_resolved else "-"
        lines.append(
            "| "
            f"{ticket.id} | [{ticket.type.upper()}] | "
            f"{ticket.priority.title()} | {ticket.area} | "
            f"[{ticket.title}]({relative_link(ticket.path, from_dir)}) | "
            f"{parent} | {blockers} | {ticket.created or '-'} | "
            f"{resolved or '-'} |"
        )
    return lines


def render_status_page(
    tickets,
    decisions,
    status,
    config,
    issues_dir,
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


def render_done_page(tickets, decisions, issues_dir) -> str:
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


def related_tickets(decision: Decision, tickets: list[Ticket]) -> list[Ticket]:
    return sorted(
        [ticket for ticket in tickets if decision.id in ticket.decisions],
        key=lambda ticket: (
            STATUS_ORDER.get(ticket.status, 99),
            ticket.id,
        ),
    )


def render_decision_ticket_table(
    decision,
    tickets,
    by_id,
    from_dir,
) -> list[str]:
    related = related_tickets(decision, tickets)
    if not related:
        return ["No related tickets."]
    lines = [
        "| Ticket | Parent epic | Current status | Blocked by |",
        "| --- | --- | --- | --- |",
    ]
    for ticket in related:
        parent = (
            linked_id(ticket.parent, by_id, from_dir)
            if ticket.parent
            else "-"
        )
        blockers = ", ".join(
            linked_id(item, by_id, from_dir)
            for item in ticket.blocked_by
        ) or "-"
        lines.append(
            f"| [{ticket.id}: {ticket.title}]"
            f"({relative_link(ticket.path, from_dir)}) | "
            f"{parent} | {status_heading(ticket.status)} | {blockers} |"
        )
    return lines


def render_decisions_page(tickets, decisions, issues_dir) -> str:
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
            render_decision_ticket_table(
                decision,
                tickets,
                by_id,
                issues_dir,
            )
        )
        lines.append("")
    return "\n".join(lines)


def updated_decision_text(decision, tickets, decisions) -> str:
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


def refresh_decision_related_work(tickets, decisions) -> None:
    for decision in decisions:
        decision.path.write_text(
            updated_decision_text(decision, tickets, decisions),
            encoding="utf-8",
        )


def _csv_code(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def render_readme(tickets, decisions, config: TrackerConfig) -> str:
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
            "| `testing_policy` | `v1` for active tickets | Requires complete Testing Impact and resolution evidence. |",
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
            "## Testing Gate",
            "",
            "Every active ticket uses `testing_policy: v1` and records exact "
            "automated tests, browser scenarios, commands, and evidence under "
            "`## Testing Impact`. Browser level is `none`, `targeted`, or "
            "`full`: small visual-only fixes may use `none`, while only "
            "`targeted` and `full` update `tests/e2e/README.md`. Before "
            "resolution, compare the implementation diff with "
            "`.claude/skills/ticket-master/"
            "TESTING_WORKFLOW.md` and record the required results.",
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
