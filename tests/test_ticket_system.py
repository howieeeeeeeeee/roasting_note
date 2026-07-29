from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = (
    ROOT / ".claude" / "skills" / "ticket-master" / "scripts"
)
SCRIPT = SCRIPT_DIR / "generate_issues_index.py"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("ticket_master_index", SCRIPT)
TRACKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TRACKER
SPEC.loader.exec_module(TRACKER)

import render_dashboard as DASHBOARD  # noqa: E402


def write_record(path: Path, frontmatter: str, body: str = "# Record\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{frontmatter.strip()}\n---\n\n{body}",
        encoding="utf-8",
    )


def write_tracker_config(issues: Path) -> None:
    issues.mkdir(parents=True, exist_ok=True)
    (issues / "tracker.toml").write_text(
        """[project]
name = "Test RoastLogger"
description = "Test tracker."
ticket_prefix = "RN"
decision_prefix = "HD"
ticket_types = ["epic", "bug", "feature", "improvement", "refactor", "todo"]
priorities = ["high", "medium", "low"]
""",
        encoding="utf-8",
    )


def write_decision(path: Path, *, status: str = "pending") -> None:
    finalized = "2026-07-29" if status == "finalized" else ""
    outcome = "ship" if status == "finalized" else ""
    write_record(
        path,
        f"""
id: HD-0001
title: Choose Example Behavior
type: human-decision
status: {status}
created: 2026-07-29
finalized: {finalized}
outcome: {outcome}
decided_by:
area: example
blocked_by: []
tags: []
""",
        """# HD-0001: Choose Example Behavior

## Related Work

<!-- BEGIN GENERATED RELATED WORK -->

No related tickets.

<!-- END GENERATED RELATED WORK -->
""",
    )


def write_epic_bundle(issues: Path) -> None:
    write_record(
        issues / "RN-0100-example-epic.md",
        """
id: RN-0100
title: Example Epic
type: epic
status: pending
priority: high
created: 2026-07-29
resolved:
area: example
parent:
decisions: []
blocked_by: []
tags: []
""",
    )
    write_record(
        issues / "RN-0100-01-evidence.md",
        """
id: RN-0100-01
title: Gather Evidence
type: todo
status: resolved
priority: high
created: 2026-07-29
resolved: 2026-07-29
area: example
parent: RN-0100
decisions: [HD-0001]
blocked_by: []
tags: []
""",
    )
    write_record(
        issues / "RN-0100-02-implement.md",
        """
id: RN-0100-02
title: Implement Outcome
type: feature
status: blocked
priority: medium
created: 2026-07-29
resolved:
area: example
parent: RN-0100
decisions: [HD-0001]
blocked_by: [HD-0001]
tags: []
""",
    )


def test_generate_files_epic_children_and_human_decision(
    tmp_path: Path,
) -> None:
    issues = tmp_path / "docs" / "issues"
    write_tracker_config(issues)
    write_epic_bundle(issues)
    write_decision(issues / "HD-0001-choose-example.md")

    ticket_count, decision_count, moved = TRACKER.generate(issues)

    assert (ticket_count, decision_count, moved) == (3, 1, 4)
    assert (issues / "pending" / "RN-0100-example-epic.md").exists()
    assert (
        issues
        / "resolved"
        / "RN-0100-example-epic"
        / "RN-0100-01-evidence.md"
    ).exists()
    assert (
        issues
        / "blocked"
        / "RN-0100-example-epic"
        / "RN-0100-02-implement.md"
    ).exists()
    assert (
        issues / "decision-pending" / "HD-0001-choose-example.md"
    ).exists()
    assert "RN-0100-02: Implement Outcome" in (
        issues / "human-decisions.md"
    ).read_text(encoding="utf-8")
    assert "Visual Overview" in (issues / "README.md").read_text(
        encoding="utf-8"
    )


def test_generator_rejects_blocked_ticket_without_blocker(
    tmp_path: Path,
) -> None:
    issues = tmp_path / "docs" / "issues"
    write_tracker_config(issues)
    write_record(
        issues / "RN-0101-invalid.md",
        """
id: RN-0101
title: Invalid Blocked Ticket
type: bug
status: blocked
priority: high
created: 2026-07-29
resolved:
area: example
parent:
decisions: []
blocked_by: []
tags: []
""",
    )

    with pytest.raises(ValueError, match="blocked status requires blocked_by"):
        TRACKER.generate(issues)


def test_generator_rejects_dependency_cycle(tmp_path: Path) -> None:
    issues = tmp_path / "docs" / "issues"
    write_tracker_config(issues)
    write_record(
        issues / "RN-0101-first.md",
        """
id: RN-0101
title: First
type: todo
status: blocked
priority: medium
created: 2026-07-29
resolved:
area: example
parent:
decisions: []
blocked_by: [RN-0102]
tags: []
""",
    )
    write_record(
        issues / "RN-0102-second.md",
        """
id: RN-0102
title: Second
type: todo
status: blocked
priority: medium
created: 2026-07-29
resolved:
area: example
parent:
decisions: []
blocked_by: [RN-0101]
tags: []
""",
    )

    with pytest.raises(ValueError, match="blocker cycle"):
        TRACKER.generate(issues)


def test_generation_is_deterministic_and_check_detects_staleness(
    tmp_path: Path,
) -> None:
    issues = tmp_path / "docs" / "issues"
    write_tracker_config(issues)
    write_epic_bundle(issues)
    write_decision(issues / "HD-0001-choose-example.md")

    TRACKER.generate(issues)
    first = (issues / TRACKER.HTML_OVERVIEW_NAME).read_bytes()
    TRACKER.generate(issues)
    second = (issues / TRACKER.HTML_OVERVIEW_NAME).read_bytes()

    assert first == second
    TRACKER.generate(issues, check=True)
    overview = issues / TRACKER.HTML_OVERVIEW_NAME
    overview.write_text(
        overview.read_text(encoding="utf-8") + "\n<!-- stale -->\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Stale generated"):
        TRACKER.generate(issues, check=True)


def test_dashboard_is_offline_safe_and_has_core_views() -> None:
    config = TRACKER.load_config()
    tickets, decisions = TRACKER.load_records()
    rendered = DASHBOARD.render_dashboard(
        config,
        tickets,
        decisions,
        TRACKER.ISSUES_DIR,
    )

    assert "__TRACKER_DATA__" not in rendered
    assert '["next", "Next"]' in rendered
    assert '["board", "Board"]' in rendered
    assert '["directory", "Directory"]' in rendered
    assert '["dependencies", "Dependencies"]' in rendered
    assert 'data-view="${id}"' in rendered
    assert "Ticket workbench" in rendered
    assert "--paper: #eef1ec" in rendered
    assert "issue-workbench-theme" in rendered
    assert "data.project.priorities" in rendered
    assert "DOMPurify.sanitize(marked.parse(" in rendered
    assert "roastlogger-ticket-theme" not in rendered
    assert "--coffee" not in rendered
    assert "__MARKED_JS__" not in rendered
    assert "__DOMPURIFY_JS__" not in rendered
    assert "__COURIER_PRIME_REGULAR__" not in rendered
    assert "__COURIER_PRIME_BOLD__" not in rendered
    assert not re.search(
        r'<(?:script|link)\b[^>]+(?:src|href)=["\']https?://',
        rendered,
    )
    escaped = DASHBOARD._safe_json(
        {"body": "</script><script>alert(1)</script>"}
    )
    assert "</script>" not in escaped
    assert "\\u003c/script\\u003e" in escaped


def test_dashboard_script_parses_as_javascript(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not available")
    html = (TRACKER.ISSUES_DIR / "overview.html").read_text(encoding="utf-8")
    scripts = re.findall(
        r"<script(?:\s[^>]*)?>(.*?)</script>",
        html,
        re.DOTALL,
    )
    assert scripts
    source = tmp_path / "overview-app.js"
    source.write_text(scripts[-1], encoding="utf-8")
    result = subprocess.run(
        [node, "--check", str(source)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_skill_and_templates_enforce_documentation_updates() -> None:
    skill_root = ROOT / ".claude" / "skills" / "ticket-master"
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    workflow = (skill_root / "DOCUMENTATION_WORKFLOW.md").read_text(
        encoding="utf-8"
    )
    assert "DOCUMENTATION_WORKFLOW.md" in skill
    assert "html/INSTRUCTIONS.md" in skill
    assert "Do not mark a ticket complete" in skill
    assert "docs/design/" in workflow
    assert "docs/architecture/api-endpoints.md" in workflow
    dashboard_guidance = (
        skill_root / "html" / "INSTRUCTIONS.md"
    ).read_text(encoding="utf-8")
    assert "Kantian ticket-system reference" in dashboard_guidance
    assert "Do not restyle the workbench" in dashboard_guidance
    for relative in (
        "html/fonts/courier-prime-regular.ttf.b64",
        "html/fonts/courier-prime-bold.ttf.b64",
        "html/vendor/marked.umd.js",
        "html/vendor/purify.min.js",
        "html/licenses/COURIER_PRIME_OFL.txt",
        "html/licenses/MARKED_LICENSE.txt",
        "html/licenses/DOMPURIFY_LICENSE.txt",
        "html/licenses/DOMPURIFY_LICENSE_MPL.txt",
    ):
        assert (skill_root / relative).stat().st_size > 0
    for name in ("TICKET.md", "HUMAN_DECISION.md"):
        bundled = skill_root / "templates" / name
        active = TRACKER.ISSUES_DIR / "templates" / name
        assert bundled.read_text(encoding="utf-8") == active.read_text(
            encoding="utf-8"
        )
