"""Enforce the repository's human-authored file-size policy."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_PHYSICAL_LINES = 1_000
INCLUDED_SUFFIXES = {".py", ".js", ".html", ".css", ".cpp", ".h", ".md"}
GENERATED_PATHS = {Path("docs/issues/overview.html")}
GENERATED_NOTICE = b"Generated from frontmatter by"


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [
        Path(path.decode())
        for path in result.stdout.split(b"\0")
        if path
    ]


def is_exempt(path: Path, content: bytes) -> bool:
    if path in GENERATED_PATHS or GENERATED_NOTICE in content:
        return True
    if "vendor" in path.parts or "licenses" in path.parts:
        return True
    if path.name.endswith((".min.js", ".min.css", ".lock")):
        return True
    return False


def physical_line_count(content: bytes) -> int:
    return len(content.splitlines())


def test_human_authored_files_do_not_exceed_line_limit():
    oversized = []
    for path in tracked_files():
        if path.suffix.lower() not in INCLUDED_SUFFIXES:
            continue
        content = (ROOT / path).read_bytes()
        if is_exempt(path, content):
            continue
        line_count = physical_line_count(content)
        if line_count > MAX_PHYSICAL_LINES:
            oversized.append(f"{path}: {line_count} lines")
    assert not oversized, (
        f"Human-authored files must not exceed {MAX_PHYSICAL_LINES} physical "
        "lines. Split each file by responsibility:\n- "
        + "\n- ".join(oversized)
    )
