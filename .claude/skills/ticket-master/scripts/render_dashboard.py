"""Render the self-contained offline issue-tracker dashboard."""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
HTML_ROOT = SKILL_ROOT / "html"
ACTIVE_TICKET_STATUSES = {"pending", "in_progress", "blocked"}


def _without_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :]).lstrip()
    return text


def _relative_source(path: Path, issues_dir: Path) -> str:
    return path.relative_to(issues_dir).as_posix()


def _ticket_payload(ticket: Any, issues_dir: Path) -> dict[str, Any]:
    return {
        "id": ticket.id,
        "title": ticket.title,
        "kind": "ticket",
        "type": ticket.type,
        "status": ticket.status,
        "priority": ticket.priority,
        "area": ticket.area,
        "created": ticket.created,
        "completed": ticket.resolved,
        "parent": ticket.parent,
        "decisions": ticket.decisions,
        "blockedBy": ticket.blocked_by,
        "tags": ticket.tags,
        "sourcePath": _relative_source(ticket.path, issues_dir),
        "markdown": _without_frontmatter(
            ticket.path.read_text(encoding="utf-8")
        ),
    }


def _decision_payload(decision: Any, issues_dir: Path) -> dict[str, Any]:
    return {
        "id": decision.id,
        "title": decision.title,
        "kind": "decision",
        "type": "human-decision",
        "status": decision.status,
        "priority": "",
        "area": decision.area,
        "created": decision.created,
        "completed": decision.finalized,
        "parent": "",
        "decisions": [],
        "blockedBy": decision.blocked_by,
        "tags": decision.tags,
        "outcome": decision.outcome,
        "decidedBy": decision.decided_by,
        "sourcePath": _relative_source(decision.path, issues_dir),
        "markdown": _without_frontmatter(
            decision.path.read_text(encoding="utf-8")
        ),
    }


def _reachable(
    record_id: str,
    by_id: dict[str, dict[str, Any]],
) -> set[str]:
    reached: set[str] = set()
    stack = list(by_id[record_id]["dependents"])
    while stack:
        current = stack.pop()
        if current in reached:
            continue
        reached.add(current)
        stack.extend(by_id[current]["dependents"])
    return reached


def build_dashboard_data(
    config: Any,
    tickets: list[Any],
    decisions: list[Any],
    issues_dir: Path,
) -> dict[str, Any]:
    records = [
        *(_ticket_payload(ticket, issues_dir) for ticket in tickets),
        *(_decision_payload(decision, issues_dir) for decision in decisions),
    ]
    by_id = {record["id"]: record for record in records}
    for record in records:
        record["dependents"] = []
    for record in records:
        for blocker_id in record["blockedBy"]:
            by_id[blocker_id]["dependents"].append(record["id"])
    for record in records:
        record["dependents"].sort()
        downstream = _reachable(record["id"], by_id)
        record["downstream"] = sorted(downstream)
        record["downstreamWork"] = sum(
            by_id[item]["kind"] == "ticket"
            and by_id[item]["status"] in ACTIVE_TICKET_STATUSES
            for item in downstream
        )
        record["downstreamDecisions"] = sum(
            by_id[item]["kind"] == "decision"
            and by_id[item]["status"] == "pending"
            for item in downstream
        )
        record["unlocksNow"] = sorted(
            item
            for item in record["dependents"]
            if len(by_id[item]["blockedBy"]) == 1
            and (
                (
                    by_id[item]["kind"] == "ticket"
                    and by_id[item]["status"] == "blocked"
                )
                or (
                    by_id[item]["kind"] == "decision"
                    and by_id[item]["status"] == "pending"
                )
            )
        )
        if record["kind"] == "decision":
            record["readiness"] = (
                "finalized"
                if record["status"] == "finalized"
                else "ready" if not record["blockedBy"] else "waiting"
            )

    for record in records:
        if record["type"] != "epic":
            continue
        children = sorted(
            (
                item
                for item in records
                if item["kind"] == "ticket"
                and item["parent"] == record["id"]
            ),
            key=lambda item: item["id"],
        )
        record["children"] = [child["id"] for child in children]
        record["childCounts"] = {
            status: sum(child["status"] == status for child in children)
            for status in (
                "pending",
                "in_progress",
                "blocked",
                "resolved",
                "wont_fix",
            )
        }

    records.sort(key=lambda item: item["id"])
    canonical = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "project": {
            "name": config.project_name,
            "description": config.description,
            "ticketPrefix": config.ticket_prefix,
            "decisionPrefix": config.decision_prefix,
            "ticketTypes": list(config.ticket_types),
            "priorities": list(config.priorities),
        },
        "summary": {
            "tickets": len(tickets),
            "decisions": len(decisions),
            "activeTickets": sum(
                record["kind"] == "ticket"
                and record["status"] in ACTIVE_TICKET_STATUSES
                for record in records
            ),
            "blockedTickets": sum(
                record["kind"] == "ticket"
                and record["status"] == "blocked"
                for record in records
            ),
            "readyDecisions": sum(
                record.get("readiness") == "ready" for record in records
            ),
            "waitingDecisions": sum(
                record.get("readiness") == "waiting" for record in records
            ),
        },
        "records": records,
        "pathIndex": {
            record["sourcePath"]: record["id"] for record in records
        },
        "sourceDigest": hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()[:12],
    }


def _safe_json(data: dict[str, Any]) -> str:
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        serialized.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _asset_text(relative: str) -> str:
    return (HTML_ROOT / relative).read_text(encoding="utf-8")


def render_dashboard(
    config: Any,
    tickets: list[Any],
    decisions: list[Any],
    issues_dir: Path,
) -> str:
    data = build_dashboard_data(config, tickets, decisions, issues_dir)
    replacements = {
        "__PROJECT_NAME__": html.escape(config.project_name),
        "__TRACKER_DATA__": _safe_json(data),
        "__COURIER_PRIME_REGULAR__": _asset_text(
            "fonts/courier-prime-regular.ttf.b64"
        ).replace("\n", ""),
        "__COURIER_PRIME_BOLD__": _asset_text(
            "fonts/courier-prime-bold.ttf.b64"
        ).replace("\n", ""),
        "__MARKED_JS__": _asset_text("vendor/marked.umd.js"),
        "__DOMPURIFY_JS__": _asset_text("vendor/purify.min.js"),
    }
    template = _asset_text("overview.template.html")
    missing = [
        placeholder
        for placeholder in replacements
        if placeholder not in template
    ]
    if missing:
        raise ValueError(f"HTML template is missing {', '.join(missing)}")
    pattern = re.compile("|".join(re.escape(item) for item in replacements))
    return pattern.sub(lambda match: replacements[match.group(0)], template)
