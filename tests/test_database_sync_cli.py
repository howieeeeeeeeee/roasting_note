"""Dry-run and two-confirmation contract tests for guarded sync."""

import io
import json
from pathlib import Path

import pytest

import scripts.sync_database as cli
import roastlogger.services.database_sync_runner as runner
from roastlogger.services.database_sync_plan import SyncRuntime
from tests.sync_fakes import FakeClient


VALUES = {
    "DEVICE": "test-mac",
    "MONGO_URI": "mongodb://online.example/roastlogger",
    "MONGO_URI_LOCAL": "mongodb://localhost:27017/roastlogger",
    "ONLINE_DB_NAME": "roastlogger",
    "LOCAL_DB_NAME": "roastlogger",
}


def make_runtime():
    return SyncRuntime.from_mapping(
        VALUES,
        direction="online-to-local",
    )


def make_plan(tmp_path):
    return {
        "run_id": "20260729T130000Z-1234abcd",
        "device": "test-mac",
        "direction": "online-to-local",
        "source": {
            "role": "online",
            "host": "online.example",
            "database": "roastlogger",
        },
        "destination": {
            "role": "local",
            "host": "localhost:27017",
            "database": "roastlogger",
        },
        "requested_collections": ["beans", "roasts"],
        "resolved_collections": ["beans", "roasts"],
        "batch_size": 500,
        "source_counts": {"beans": 1, "roasts": 1},
        "destination_counts": {"beans": 0, "roasts": 0},
        "backup": {
            "scope": "complete_destination_database",
            "collections": ["beans", "roasts", "other"],
            "counts": {"beans": 0, "roasts": 0, "other": 2},
            "path": str(tmp_path / "db_backup" / "complete"),
        },
        "audit_path": str(tmp_path / "docs" / "audit.json"),
        "cli_command": (
            "uv run python scripts/sync_database.py "
            "--direction online-to-local"
        ),
    }


def test_cli_dry_run_prints_plan_without_prompt_or_runner(
    monkeypatch,
    tmp_path,
):
    created_clients = []

    def fake_client(uri):
        client = FakeClient()
        created_clients.append((uri, client))
        return client

    monkeypatch.setattr(cli, "load_runtime_values", lambda: VALUES)
    monkeypatch.setattr(cli, "MongoClient", fake_client)
    monkeypatch.setattr(
        cli,
        "build_preflight",
        lambda *args, **kwargs: make_plan(tmp_path),
    )
    monkeypatch.setattr(
        cli,
        "run_guarded_sync",
        lambda *args, **kwargs: pytest.fail("dry run invoked applied runner"),
    )
    output = io.StringIO()

    exit_code = cli.main(
        ["--direction", "online-to-local", "--dry-run"],
        prompt=lambda _: pytest.fail("dry run prompted"),
        output=output,
    )

    assert exit_code == 0
    rendered = output.getvalue()
    assert '"complete_destination_database"' in rendered
    assert "online.example" in rendered
    assert "mongodb://" not in rendered
    assert len(created_clients) == 2
    assert all(client.closed for _, client in created_clients)


def test_cli_has_no_confirmation_bypass_and_requires_positive_batch():
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["--direction", "online-to-local", "--yes"]
        )
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--direction",
                "online-to-local",
                "--batch-size",
                "0",
            ]
        )


def test_first_confirmation_mismatch_has_no_backup_sync_or_audit(
    tmp_path,
):
    calls = {"backup": 0, "sync": 0}

    def backup(*args):
        calls["backup"] += 1

    def synchronize(*args):
        calls["sync"] += 1

    result = runner.run_guarded_sync(
        make_runtime(),
        FakeClient(),
        FakeClient(),
        tmp_path,
        make_plan(tmp_path),
        prompt=lambda _: "wrong",
        backup=backup,
        synchronize=synchronize,
    )

    assert result["status"] == "cancelled_before_backup"
    assert calls == {"backup": 0, "sync": 0}
    assert not (tmp_path / "docs").exists()


def test_second_confirmation_mismatch_audits_after_complete_backup(
    tmp_path,
):
    prompts = iter(
        [
            "BACKUP 20260729T130000Z-1234abcd",
            "wrong",
        ]
    )
    backup_path = tmp_path / "db_backup" / "complete"

    result = runner.run_guarded_sync(
        make_runtime(),
        FakeClient(),
        FakeClient(),
        tmp_path,
        make_plan(tmp_path),
        prompt=lambda _: next(prompts),
        backup=lambda *args: {
            "path": str(backup_path),
            "status": "complete",
            "manifest_sha256": "abc",
            "collection_count": 3,
            "document_count": 2,
            "collections": [],
        },
        synchronize=lambda *args: pytest.fail("sync ran before APPLY token"),
    )

    assert result["status"] == "cancelled_after_backup"
    audit = json.loads(Path(result["audit_path"]).read_text())
    assert audit["status"] == "cancelled_after_backup"
    assert audit["backup"]["status"] == "complete"


def test_backup_failure_writes_terminal_audit_without_sync(tmp_path):
    prompts = iter(["BACKUP 20260729T130000Z-1234abcd"])
    result = runner.run_guarded_sync(
        make_runtime(),
        FakeClient(),
        FakeClient(),
        tmp_path,
        make_plan(tmp_path),
        prompt=lambda _: next(prompts),
        backup=lambda *args: (_ for _ in ()).throw(
            RuntimeError("credential-bearing failure")
        ),
        synchronize=lambda *args: pytest.fail("sync ran after backup failure"),
    )

    assert result["status"] == "backup_failed"
    audit = json.loads(Path(result["audit_path"]).read_text())
    assert audit["status"] == "backup_failed"
    assert audit["backup"]["status"] == "incomplete"
    assert "credential-bearing" not in json.dumps(audit)
    assert "mongodb://" not in json.dumps(audit)


def test_partial_sync_failure_records_completed_work_and_stops(tmp_path):
    prompts = iter(
        [
            "BACKUP 20260729T130000Z-1234abcd",
            "APPLY online-to-local 20260729T130000Z-1234abcd",
        ]
    )
    completed = {
        "beans": {
            "added": 1,
            "updated": 0,
            "skipped": 0,
            "conflicts": 0,
            "post_run_count": 1,
        }
    }
    failure = runner.SyncExecutionError(
        "roasts",
        completed,
        RuntimeError("driver details"),
    )
    result = runner.run_guarded_sync(
        make_runtime(),
        FakeClient(),
        FakeClient(),
        tmp_path,
        make_plan(tmp_path),
        prompt=lambda _: next(prompts),
        backup=lambda *args: {
            "path": str(tmp_path / "db_backup" / "complete"),
            "status": "complete",
            "manifest_sha256": "abc",
            "collection_count": 0,
            "document_count": 0,
            "collections": [],
        },
        synchronize=lambda *args: (_ for _ in ()).throw(failure),
    )

    assert result["status"] == "partial_sync_failed"
    audit = json.loads(Path(result["audit_path"]).read_text())
    assert audit["sync"]["failed_collection"] == "roasts"
    assert audit["sync"]["collections"] == completed
    assert audit["sync"]["verified"] is False


def test_exact_tokens_allow_sync_and_write_one_success_audit(tmp_path):
    prompts = iter(
        [
            "BACKUP 20260729T130000Z-1234abcd",
            "APPLY online-to-local 20260729T130000Z-1234abcd",
        ]
    )
    backup_path = tmp_path / "db_backup" / "complete"
    result = runner.run_guarded_sync(
        make_runtime(),
        FakeClient(),
        FakeClient(),
        tmp_path,
        make_plan(tmp_path),
        prompt=lambda _: next(prompts),
        backup=lambda *args: {
            "path": str(backup_path),
            "status": "complete",
            "manifest_sha256": "abc",
            "collection_count": 3,
            "document_count": 2,
            "collections": [],
        },
        synchronize=lambda *args: {
            "collections": {
                "beans": {
                    "added": 1,
                    "updated": 0,
                    "skipped": 0,
                    "conflicts": 0,
                    "post_run_count": 1,
                }
            },
            "aggregate": {
                "added": 1,
                "updated": 0,
                "skipped": 0,
                "conflicts": 0,
            },
            "verified": True,
        },
    )

    assert result["status"] == "success"
    records = list((tmp_path / "docs").rglob("*.json"))
    assert records == [Path(result["audit_path"])]
    audit = json.loads(records[0].read_text())
    assert audit["DEVICE"] == "test-mac"
    assert audit["sync"]["aggregate"]["added"] == 1
    assert audit["git"]["commit"]


def test_audit_failure_after_activity_writes_untracked_recovery(
    monkeypatch,
    tmp_path,
):
    prompts = iter(
        [
            "BACKUP 20260729T130000Z-1234abcd",
            "APPLY online-to-local 20260729T130000Z-1234abcd",
        ]
    )
    backup_path = tmp_path / "db_backup" / "complete"
    monkeypatch.setattr(
        runner,
        "write_applied_audit",
        lambda *args: (_ for _ in ()).throw(OSError("read-only docs")),
    )

    result = runner.run_guarded_sync(
        make_runtime(),
        FakeClient(),
        FakeClient(),
        tmp_path,
        make_plan(tmp_path),
        prompt=lambda _: next(prompts),
        backup=lambda *args: {
            "path": str(backup_path),
            "status": "complete",
            "manifest_sha256": "abc",
            "collection_count": 0,
            "document_count": 0,
            "collections": [],
        },
        synchronize=lambda *args: {
            "collections": {},
            "aggregate": {
                "added": 0,
                "updated": 0,
                "skipped": 0,
                "conflicts": 0,
            },
            "verified": True,
        },
    )

    assert result["exit_code"] == 2
    assert Path(result["recovery_path"]).is_file()
    assert "db_backup" in result["recovery_path"]
