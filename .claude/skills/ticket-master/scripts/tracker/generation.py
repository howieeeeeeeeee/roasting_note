"""Tracker generation and stale-output checks."""

from __future__ import annotations

from pathlib import Path

from render_dashboard import render_dashboard

from .filing import file_records
from .records import (
    ACTIVE_TICKET_STATUSES,
    HTML_OVERVIEW_NAME,
    ISSUES_DIR,
    OVERVIEW_NAMES,
    ROOT,
    load_config,
    load_records,
)
from .rendering import (
    refresh_decision_related_work,
    render_decisions_page,
    render_done_page,
    render_readme,
    render_status_page,
    updated_decision_text,
)
from .validation import validate_metadata, validate_paths


def generated_files(tickets, decisions, config, issues_dir) -> dict[Path, str]:
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


def check_generated(tickets, decisions, config, issues_dir) -> None:
    def display_path(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)

    stale = []
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
