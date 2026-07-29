"""Guarded operational CLI for timestamp-aware database synchronization."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from roastlogger.config import default_config
from roastlogger.services.database_sync_plan import (
    DIRECTIONS,
    KNOWN_COLLECTIONS,
    SyncRuntime,
    build_preflight,
    sanitize_failure,
)
from roastlogger.services.database_sync_runner import run_guarded_sync


def positive_integer(value):
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser():
    parser = argparse.ArgumentParser(
        description="Preview or apply a guarded RoastLogger database sync.",
    )
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument(
        "--collection",
        action="append",
        choices=KNOWN_COLLECTIONS,
        dest="collections",
    )
    parser.add_argument("--batch-size", type=positive_integer, default=500)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def load_runtime_values():
    values = default_config()
    values.update(
        {
            key: value
            for key, value in dotenv_values(ROOT / ".env").items()
            if value is not None
        }
    )
    return values


def _print_plan(plan, output):
    print(json.dumps(plan, indent=2, sort_keys=True), file=output)


def _print_result(result, output):
    print(json.dumps(result, indent=2, sort_keys=True), file=output)
    if result.get("recovery_path"):
        print(
            f"AUDIT RECOVERY REQUIRED: {result['recovery_path']}",
            file=output,
        )
    elif result.get("audit_path"):
        path = result["audit_path"]
        print("Review the audit record, then publish only that file:", file=output)
        print(f"git add -- {path}", file=output)
        print(
            'git commit -m "docs(audit): record database mirror"',
            file=output,
        )


def main(argv=None, *, prompt=input, output=sys.stdout):
    args = build_parser().parse_args(argv)
    online_client = None
    local_client = None
    try:
        runtime = SyncRuntime.from_mapping(
            load_runtime_values(),
            direction=args.direction,
            collections=args.collections,
            batch_size=args.batch_size,
        )
        online_uri = (
            runtime.source_uri
            if runtime.source_role == "online"
            else runtime.destination_uri
        )
        local_uri = (
            runtime.source_uri
            if runtime.source_role == "local"
            else runtime.destination_uri
        )
        online_client = MongoClient(online_uri)
        local_client = MongoClient(local_uri)
        source_client = (
            online_client if runtime.source_role == "online" else local_client
        )
        destination_client = (
            online_client
            if runtime.destination_role == "online"
            else local_client
        )
        plan = build_preflight(
            runtime,
            source_client,
            destination_client,
            ROOT,
        )
        _print_plan(plan, output)
        if args.dry_run:
            return 0
        result = run_guarded_sync(
            runtime,
            source_client,
            destination_client,
            ROOT,
            plan,
            prompt=prompt,
        )
        _print_result(result, output)
        return result["exit_code"]
    except Exception as error:
        print(
            json.dumps({"success": False, "error": sanitize_failure(error)}),
            file=output,
        )
        return 2
    finally:
        if online_client is not None:
            online_client.close()
        if local_client is not None:
            local_client.close()


if __name__ == "__main__":
    raise SystemExit(main())
