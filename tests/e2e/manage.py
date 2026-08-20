"""Start and clean up the dedicated RoastLogger E2E runtime."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from dotenv import dotenv_values
from pymongo import MongoClient

from roastlogger.e2e import E2E_DATABASE_NAME, validate_run_id
from tests.e2e.cleanup import cleanup_run


ROOT = Path(__file__).resolve().parents[2]
E2E_ROOT = ROOT / "tests" / "e2e"


def _load_local_uri():
    values = dotenv_values(ROOT / ".env")
    return values.get("MONGO_URI_LOCAL") or "mongodb://localhost:27017/"


def _paths(run_id):
    return (
        E2E_ROOT / "artifacts" / run_id,
        E2E_ROOT / "runtime" / run_id,
    )


def _wait_for(url, processes, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for process in processes:
            if process.poll() is not None:
                raise RuntimeError("an E2E service exited during startup")
        try:
            with urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, URLError):
            time.sleep(0.1)
    raise RuntimeError(f"timed out waiting for {url}")


def _summary(artifact_root, run_id, app_url, sensor_url, *, sync_fake):
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    ).stdout.strip()
    content = f"""# RoastLogger E2E Run

- Run ID: `{run_id}`
- Commit: `{commit or "unavailable"}`
- App URL: `{app_url}`
- Sensor URL: `{sensor_url}`
- Guarded sync executor: `{"artifact-only fake" if sync_fake else "disabled"}`
- Scenarios: pending
- Browser assertions: pending
- Console/network failures: pending
- Cleanup: pending

## Evidence

- Screenshots: `screenshots/`
- Service logs: `app.log`, `sensor.log`
"""
    (artifact_root / "summary.md").write_text(content, encoding="utf-8")


def start(args):
    run_id = validate_run_id(args.run_id)
    if args.database != E2E_DATABASE_NAME:
        raise ValueError(f"start requires database {E2E_DATABASE_NAME}")
    artifact_root, runtime_root = _paths(run_id)
    artifact_root.mkdir(parents=True, exist_ok=False)
    runtime_root.mkdir(parents=True, exist_ok=False)
    (artifact_root / "screenshots").mkdir()

    app_url = f"http://127.0.0.1:{args.app_port}"
    sensor_base = f"http://127.0.0.1:{args.sensor_port}"
    sensor_url = f"{sensor_base}/temp"
    environment = os.environ.copy()
    environment.update(
        {
            "DEFAULT_DB": "local",
            "DEVICE": f"e2e-{run_id[:59]}",
            "E2E_MODE": "1",
            "E2E_RUN_ID": run_id,
            "E2E_ARTIFACT_ROOT": str(artifact_root),
            "E2E_APP_PORT": str(args.app_port),
            "LOCAL_DB_NAME": E2E_DATABASE_NAME,
            "MONGO_URI": "disabled://e2e-online",
            "MONGO_URI_LOCAL": _load_local_uri(),
            "TEMP_SENSOR_URL": sensor_url,
        }
    )
    environment.pop("E2E_SYNC_FAKE", None)
    if getattr(args, "sync_fake", False):
        environment["E2E_SYNC_FAKE"] = "1"
    _summary(
        artifact_root,
        run_id,
        app_url,
        sensor_url,
        sync_fake=getattr(args, "sync_fake", False),
    )
    state = {
        "run_id": run_id,
        "app_url": app_url,
        "sensor_url": sensor_url,
        "artifact_root": str(artifact_root),
    }
    (runtime_root / "state.json").write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )

    app_log = (artifact_root / "app.log").open("w", encoding="utf-8")
    sensor_log = (artifact_root / "sensor.log").open("w", encoding="utf-8")
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "tests.e2e.sensor_server",
                "--port",
                str(args.sensor_port),
            ],
            cwd=ROOT,
            env=environment,
            stdout=sensor_log,
            stderr=subprocess.STDOUT,
            text=True,
        ),
        subprocess.Popen(
            [sys.executable, "-m", "tests.e2e.app_server"],
            cwd=ROOT,
            env=environment,
            stdout=app_log,
            stderr=subprocess.STDOUT,
            text=True,
        ),
    ]
    stopping = False

    def stop_services(*_):
        nonlocal stopping
        stopping = True
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGINT, stop_services)
    signal.signal(signal.SIGTERM, stop_services)
    try:
        _wait_for(f"{sensor_base}/health", processes)
        _wait_for(app_url, processes)
        print(json.dumps(state, indent=2))
        while not stopping and all(
            process.poll() is None for process in processes
        ):
            time.sleep(0.25)
    finally:
        stop_services()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        app_log.close()
        sensor_log.close()


def cleanup(args):
    run_id = validate_run_id(args.run_id)
    if args.database != E2E_DATABASE_NAME:
        raise ValueError(f"cleanup requires database {E2E_DATABASE_NAME}")
    artifact_root, _ = _paths(run_id)
    client = MongoClient(_load_local_uri())
    try:
        result = cleanup_run(
            client[args.database],
            run_id,
            artifact_root / "temp_logs",
        )
    finally:
        client.close()
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    start_parser = subparsers.add_parser("start")
    cleanup_parser = subparsers.add_parser("cleanup")
    for command_parser in (start_parser, cleanup_parser):
        command_parser.add_argument("--run-id", required=True)
        command_parser.add_argument(
            "--database",
            default=E2E_DATABASE_NAME,
        )
    start_parser.add_argument("--app-port", type=int, default=5011)
    start_parser.add_argument("--sensor-port", type=int, default=5012)
    start_parser.add_argument(
        "--sync-fake",
        action="store_true",
        help="inject the artifact-only guarded-sync fake executor",
    )
    start_parser.set_defaults(handler=start)
    cleanup_parser.set_defaults(handler=cleanup)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"E2E command failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
