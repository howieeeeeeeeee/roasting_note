"""Restorability and failure-state tests for destination backups."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from bson import json_util
from bson.decimal128 import Decimal128
from bson.objectid import ObjectId

from roastlogger.services.database_backup import (
    BackupVerificationError,
    backup_destination_database,
    decode_collection_name,
    verify_backup_result,
)
from roastlogger.services.database_sync_plan import SyncRuntime
from tests.sync_fakes import FakeClient, FakeCollection, FakeDatabase


def make_runtime():
    return SyncRuntime.from_mapping(
        {
            "DEVICE": "test-mac",
            "MONGO_URI": "mongodb://online.example/roastlogger",
            "MONGO_URI_LOCAL": "mongodb://localhost:27017/roastlogger",
            "ONLINE_DB_NAME": "roastlogger",
            "LOCAL_DB_NAME": "roastlogger",
        },
        direction="online-to-local",
        collections=["beans"],
    )


def test_complete_backup_round_trips_bson_and_covers_all_collections(tmp_path):
    document = {
        "_id": ObjectId(),
        "created_at": datetime(2026, 7, 29, tzinfo=timezone.utc),
        "price": Decimal128("12.34"),
        "nested": {"values": [1, "two"]},
        "archived": True,
    }
    client = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection([document]),
                    "excluded/collection": FakeCollection(
                        [{"_id": ObjectId(), "value": "kept"}]
                    ),
                }
            )
        }
    )

    result = backup_destination_database(
        make_runtime(),
        client,
        tmp_path,
        "20260729T110000Z-feedface",
    )

    backup_path = Path(result["path"])
    manifest = json.loads((backup_path / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert len(manifest["destination"]["endpoint_fingerprint"]) == 64
    assert "mongodb://" not in json.dumps(manifest)
    assert manifest["collection_count"] == 2
    assert manifest["document_count"] == 2
    assert not backup_path.with_name(f"{backup_path.name}.partial").exists()
    names = {entry["name"] for entry in manifest["collections"]}
    assert names == {"beans", "excluded/collection"}

    beans_entry = next(
        item for item in manifest["collections"] if item["name"] == "beans"
    )
    payload_path = backup_path / beans_entry["filename"]
    payload = payload_path.read_bytes()
    restored = json_util.loads(payload.decode().strip())
    assert restored["_id"] == document["_id"]
    assert restored["created_at"] == document["created_at"].replace(tzinfo=None)
    assert restored["price"] == document["price"]
    assert restored["nested"] == document["nested"]
    assert restored["archived"] is True
    assert hashlib.sha256(payload).hexdigest() == beans_entry["sha256"]
    assert len(payload) == beans_entry["bytes"]
    assert (
        decode_collection_name(beans_entry["filename"].removesuffix(".jsonl"))
        == "beans"
    )


def test_failed_backup_stays_partial_and_cannot_look_restorable(tmp_path):
    client = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection(
                        [{"_id": ObjectId()}],
                        fail_find=True,
                    )
                }
            )
        }
    )
    run_id = "20260729T120000Z-bad0cafe"

    with pytest.raises(RuntimeError, match="simulated"):
        backup_destination_database(make_runtime(), client, tmp_path, run_id)

    partials = list(tmp_path.rglob("*.partial"))
    assert len(partials) == 1
    assert (partials[0] / "failure.json").exists()
    assert not (partials[0] / "manifest.json").exists()
    failure = json.loads((partials[0] / "failure.json").read_text())
    assert failure["status"] == "incomplete"
    assert "credential" not in json.dumps(failure)


def test_completed_backup_is_reverified_before_resumed_apply(tmp_path):
    client = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {"beans": FakeCollection([{"_id": ObjectId()}])}
            )
        }
    )
    runtime = make_runtime()
    run_id = "20260820T140000Z-aabbccdd"
    result = backup_destination_database(runtime, client, tmp_path, run_id)

    verified = verify_backup_result(runtime, tmp_path, run_id, result)

    assert verified["status"] == "complete"
    entry = result["collections"][0]
    Path(result["path"], entry["filename"]).write_text("tampered\n")
    with pytest.raises(BackupVerificationError, match="checksum or count"):
        verify_backup_result(runtime, tmp_path, run_id, result)


def test_completed_backup_rejects_destination_endpoint_drift(tmp_path):
    client = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {"beans": FakeCollection([{"_id": ObjectId()}])}
            )
        }
    )
    runtime = make_runtime()
    run_id = "20260820T141000Z-bbccddee"
    result = backup_destination_database(runtime, client, tmp_path, run_id)
    drifted_runtime = SyncRuntime.from_mapping(
        {
            "DEVICE": "test-mac",
            "MONGO_URI": "mongodb://online.example/roastlogger",
            "MONGO_URI_LOCAL": (
                "mongodb://localhost:27017/roastlogger"
                "?directConnection=true"
            ),
            "ONLINE_DB_NAME": "roastlogger",
            "LOCAL_DB_NAME": "roastlogger",
        },
        direction="online-to-local",
        collections=["beans"],
    )

    with pytest.raises(BackupVerificationError, match="identity"):
        verify_backup_result(drifted_runtime, tmp_path, run_id, result)
