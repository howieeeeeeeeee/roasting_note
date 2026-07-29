#!/usr/bin/env python3
"""Compatibility entry point for the repository-local ticket system."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / ".claude"
    / "skills"
    / "ticket-master"
    / "scripts"
    / "generate_issues_index.py"
)

sys.path.insert(0, str(SCRIPT.parent))
runpy.run_path(str(SCRIPT), run_name="__main__")
