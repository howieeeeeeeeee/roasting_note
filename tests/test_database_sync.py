"""Validation, preflight, direction, and execution tests for guarded sync."""

from datetime import datetime

import pytest
from bson.objectid import ObjectId

from roastlogger.services.database_sync import (
    forecast_sync_collection,
    sync_collection,
)
from roastlogger.services.database_sync_plan import (
    SyncRuntime,
    SyncSafetyError,
    build_preflight,
)
from roastlogger.services.database_sync_runner import synchronize_collections
from tests.sync_fakes import FakeClient, FakeCollection, FakeDatabase


def runtime_values(**overrides):
    values = {
        "DEVICE": "test-mac",
        "MONGO_URI": "mongodb://online.example/roastlogger",
        "MONGO_URI_LOCAL": "mongodb://localhost:27017/roastlogger",
        "ONLINE_DB_NAME": "roastlogger",
        "LOCAL_DB_NAME": "roastlogger",
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("values", "message"),
    [
        (runtime_values(DEVICE=""), "DEVICE is required"),
        (
            runtime_values(DEVICE="../unsafe"),
            "DEVICE must use",
        ),
        (
            runtime_values(
                MONGO_URI="mongodb://user:one@same.example/db",
                MONGO_URI_LOCAL="mongodb://user:two@same.example/db",
            ),
            "same endpoint",
        ),
        (
            runtime_values(LOCAL_DB_NAME="../unsafe"),
            "database name is unsafe",
        ),
    ],
)
def test_runtime_rejects_unsafe_configuration(values, message):
    with pytest.raises(SyncSafetyError, match=message):
        SyncRuntime.from_mapping(values, direction="online-to-local")


def test_runtime_rejects_unknown_collection_and_invalid_batch_size():
    with pytest.raises(SyncSafetyError, match="unknown sync collections"):
        SyncRuntime.from_mapping(
            runtime_values(),
            direction="online-to-local",
            collections=["profiles"],
        )
    with pytest.raises(SyncSafetyError, match="positive integer"):
        SyncRuntime.from_mapping(
            runtime_values(),
            direction="online-to-local",
            batch_size=0,
        )


@pytest.mark.parametrize(
    ("direction", "source_role", "destination_role"),
    [
        ("online-to-local", "online", "local"),
        ("local-to-online", "local", "online"),
    ],
)
def test_preflight_resolves_both_directions_without_writes(
    tmp_path,
    direction,
    source_role,
    destination_role,
):
    source_bean = {"_id": ObjectId(), "archived": False}
    archived = {"_id": ObjectId(), "archived": True}
    source = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection([source_bean, archived]),
                    "roasts": FakeCollection(),
                }
            )
        }
    )
    destination = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection([archived]),
                    "roasts": FakeCollection(),
                    "private_notes": FakeCollection([source_bean]),
                }
            )
        }
    )
    runtime = SyncRuntime.from_mapping(
        runtime_values(),
        direction=direction,
    )

    plan = build_preflight(
        runtime,
        source,
        destination,
        tmp_path,
        run_id="20260729T100000Z-deadbeef",
    )

    assert plan["source"]["role"] == source_role
    assert plan["destination"]["role"] == destination_role
    assert plan["source_counts"]["beans"] == 1
    assert plan["backup"]["collections"] == [
        "beans",
        "private_notes",
        "roasts",
    ]
    assert plan["backup"]["counts"]["private_notes"] == 1
    assert plan["forecast"]["aggregate"] == {
        "source_documents": 1,
        "destination_documents": 1,
        "added": 1,
        "updated": 0,
        "unchanged": 0,
        "destination_only": 1,
        "conflicts": 0,
        "will_change": 1,
        "will_stay_unchanged": 1,
        "destination_after": 2,
    }
    assert not (tmp_path / "db_backup").exists()
    assert all(
        collection.write_count == 0
        for database in (source["roastlogger"], destination["roastlogger"])
        for collection in database.collections.values()
    )


def test_forecast_exactly_matches_timestamp_sync_without_writes():
    older = datetime(2026, 8, 20, 10, 0, 0)
    newer = datetime(2026, 8, 20, 11, 0, 0)
    add_id, update_id, unchanged_id = ObjectId(), ObjectId(), ObjectId()
    conflict_id, archived_id, destination_only_id = (
        ObjectId(),
        ObjectId(),
        ObjectId(),
    )
    source_documents = [
        {"_id": add_id, "updated_at": newer, "archived": False},
        {"_id": update_id, "updated_at": newer, "archived": False},
        {"_id": unchanged_id, "updated_at": older, "archived": False},
        {"_id": conflict_id, "archived": False},
        {"_id": archived_id, "updated_at": newer, "archived": True},
    ]
    destination_documents = [
        {"_id": update_id, "updated_at": older},
        {"_id": unchanged_id, "updated_at": newer},
        {"_id": conflict_id, "updated_at": older},
        {"_id": destination_only_id, "updated_at": newer},
    ]
    source = FakeCollection(source_documents)
    destination = FakeCollection(destination_documents)

    forecast = forecast_sync_collection(source, destination, batch_size=17)

    assert forecast == {
        "source_documents": 4,
        "destination_documents": 4,
        "added": 1,
        "updated": 1,
        "unchanged": 1,
        "destination_only": 1,
        "conflicts": 1,
        "will_change": 2,
        "will_stay_unchanged": 3,
        "destination_after": 5,
    }
    assert destination.write_count == 0

    result = sync_collection(source, destination, batch_size=17)

    assert result["added"] == forecast["added"]
    assert result["updated"] == forecast["updated"]
    assert result["skipped"] == forecast["unchanged"]
    assert result["conflicts"] == forecast["conflicts"]
    assert destination.count_documents({}) == forecast["destination_after"]
    assert destination.documents[destination_only_id]
    assert archived_id not in destination.documents


def test_unavailable_endpoint_failure_is_credential_free(tmp_path):
    runtime = SyncRuntime.from_mapping(
        runtime_values(),
        direction="online-to-local",
    )
    with pytest.raises(SyncSafetyError) as failure:
        build_preflight(
            runtime,
            FakeClient(available=False),
            FakeClient(),
            tmp_path,
        )
    assert "online endpoint is unavailable" in str(failure.value)
    assert "mongodb://" not in str(failure.value)


def test_sequential_sync_stops_after_first_failed_collection():
    now = datetime(2026, 7, 29, 10, 0, 0)
    bean = {"_id": ObjectId(), "updated_at": now, "archived": False}
    roast = {"_id": ObjectId(), "updated_at": now, "archived": False}
    source = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection([bean]),
                    "roasts": FakeCollection([roast], fail_find=True),
                }
            )
        }
    )
    destination = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection(),
                    "roasts": FakeCollection(),
                }
            )
        }
    )
    runtime = SyncRuntime.from_mapping(
        runtime_values(),
        direction="online-to-local",
        batch_size=17,
    )

    with pytest.raises(RuntimeError, match="roasts") as failure:
        synchronize_collections(runtime, source, destination)

    assert set(failure.value.completed) == {"beans"}
    assert destination["roastlogger"]["beans"].write_count == 1
    assert destination["roastlogger"]["roasts"].write_count == 0


def test_local_to_online_sync_writes_only_online_destination():
    now = datetime(2026, 7, 29, 10, 0, 0)
    bean = {"_id": ObjectId(), "updated_at": now, "archived": False}
    local = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection([bean]),
                    "roasts": FakeCollection(),
                }
            )
        }
    )
    online = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection(),
                    "roasts": FakeCollection(),
                }
            )
        }
    )
    runtime = SyncRuntime.from_mapping(
        runtime_values(),
        direction="local-to-online",
    )

    result = synchronize_collections(runtime, local, online)

    assert result["aggregate"]["added"] == 1
    assert online["roastlogger"]["beans"].write_count == 1
    assert local["roastlogger"]["beans"].write_count == 0
