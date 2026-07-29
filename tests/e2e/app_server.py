"""Loopback-only application server for a validated E2E environment."""

from __future__ import annotations

import os

from roastlogger import create_app


def main():
    port = int(os.environ.get("E2E_APP_PORT", "5011"))
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=port,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
