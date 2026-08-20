"""Loopback-only application server for a validated E2E environment."""

from __future__ import annotations

import os
from pathlib import Path

from roastlogger import create_app


def main():
    port = int(os.environ.get("E2E_APP_PORT", "5011"))
    overrides = None
    if os.environ.get("E2E_SYNC_FAKE") == "1":
        from tests.e2e.sync_fake import E2ESyncExecutor

        artifact_root = Path(os.environ["E2E_ARTIFACT_ROOT"]).resolve()
        allowed_root = (Path(__file__).parent / "artifacts").resolve()
        if not artifact_root.is_relative_to(allowed_root):
            raise RuntimeError("E2E sync fake requires a run-scoped artifact root")
        overrides = {
            "E2E_SYNC_EXECUTOR": E2ESyncExecutor(artifact_root)
        }
    app = create_app(overrides)
    app.run(
        host="127.0.0.1",
        port=port,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
