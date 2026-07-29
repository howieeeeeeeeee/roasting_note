#!/usr/bin/env python3
"""Validate, file, and render RoastLogger issue-tracker records."""

from __future__ import annotations

import argparse

from tracker.filing import file_records
from tracker.generation import check_generated, generate, generated_files
from tracker.records import (
    ACTIVE_TICKET_STATUSES,
    COMPLETED_TICKET_STATUSES,
    CONFIG_NAME,
    DECISION_STATUSES,
    GENERATED_NAMES,
    GEN_NOTE,
    HTML_OVERVIEW_NAME,
    ISSUES_DIR,
    Metadata,
    OVERVIEW_NAMES,
    RELATED_END,
    RELATED_START,
    ROOT,
    SKILL_ROOT,
    STATUS_ALIASES,
    STATUS_ORDER,
    TEMPLATE_NAMES,
    TICKET_STATUSES,
    Decision,
    Record,
    Ticket,
    TrackerConfig,
    load_config,
    load_records,
    metadata_list,
    parse_frontmatter,
    record_map,
)
from tracker.rendering import (
    completed_sort_key,
    linked_id,
    refresh_decision_related_work,
    related_tickets,
    relative_link,
    render_decision_ticket_table,
    render_decisions_page,
    render_done_page,
    render_readme,
    render_status_page,
    render_ticket_table,
    status_heading,
    ticket_sort_key,
    updated_decision_text,
)
from tracker.validation import desired_paths, validate_metadata, validate_paths


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
