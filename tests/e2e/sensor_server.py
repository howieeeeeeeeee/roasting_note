"""Loopback-only deterministic sensor server."""

from __future__ import annotations

import argparse

from tests.e2e.virtual_sensor import create_sensor_app


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5012)
    args = parser.parse_args(argv)
    create_sensor_app().run(
        host="127.0.0.1",
        port=args.port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()
