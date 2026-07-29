"""Dedicated E2E database, marker, fail-closed, and cleanup tests."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from uuid import uuid4

import pytest
from bson.objectid import ObjectId
from pymongo import MongoClient

from roastlogger import create_app
import roastlogger.database as database_module
from roastlogger.e2e import E2EConfigError, E2E_DATABASE_NAME
from tests.e2e.cleanup import CleanupSafetyError, cleanup_run
from tests.e2e.manage import start
from tests.sync_fakes import FakeClient


def e2e_config(tmp_path, run_id="runtime-test"):
    return {
        "TESTING": True,
        "DEVICE": "e2e-test",
        "E2E_MODE": True,
        "E2E_RUN_ID": run_id,
        "E2E_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
        "LOCAL_DB_NAME": E2E_DATABASE_NAME,
        "MONGO_URI": "mongodb://user:password@online.invalid/secret",
        "MONGO_URI_LOCAL": "mongodb://127.0.0.1:27017/",
        "TEMP_SENSOR_URL": "http://127.0.0.1:5012/temp",
    }


def test_e2e_factory_constructs_only_the_local_client(monkeypatch, tmp_path):
    constructed = []

    def recording_client(uri):
        constructed.append(uri)
        return FakeClient()

    monkeypatch.setattr(database_module, "MongoClient", recording_client)
    app = create_app(e2e_config(tmp_path))

    assert constructed == ["mongodb://127.0.0.1:27017/"]
    connections = app.extensions["roastlogger_databases"]
    assert connections.online_client is None
    assert connections.online_db is None
    assert connections.local_db is not None
    response = app.test_client().get("/api/settings/db")
    assert response.json == {
        "mode": "local",
        "default": "local",
        "e2e_mode": True,
        "local_database": E2E_DATABASE_NAME,
        "test_run_id": "runtime-test",
    }


@pytest.mark.parametrize(
    "override",
    [
        {"LOCAL_DB_NAME": "roastlogger"},
        {"MONGO_URI_LOCAL": "mongodb://database.example:27017/"},
        {"TEMP_SENSOR_URL": "http://sensor.example/temp"},
        {"E2E_RUN_ID": "../unsafe"},
    ],
)
def test_e2e_factory_rejects_unsafe_configuration(tmp_path, override):
    config = e2e_config(tmp_path)
    config.update(override)
    with pytest.raises(E2EConfigError):
        create_app(config)


def test_e2e_routes_reject_online_sync_and_global_cleanup(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(database_module, "MongoClient", lambda uri: FakeClient())
    app = create_app(e2e_config(tmp_path))
    client = app.test_client()

    online_mode = client.post("/api/settings/db", json={"mode": "online"})
    assert online_mode.status_code == 409
    for direction in ("online-to-local", "local-to-online"):
        legacy = client.post(f"/api/sync/{direction}")
        assert legacy.status_code == 409
        assert "disabled in E2E mode" in legacy.json["error"]
        preflight = client.post(f"/api/sync/preflight/{direction}")
        assert preflight.status_code == 503
        assert preflight.json["audit_recorded"] is True
        assert "disabled in E2E mode" in preflight.json["error"]["message"]
    for route in ("/api/db/clean-test-data", "/api/db/clean-local"):
        response = client.post(route)
        assert response.status_code == 409
        assert "run-scoped E2E cleanup" in response.json["error"]

    records = list((tmp_path / "artifacts").rglob("*.json"))
    assert len(records) == 2
    rendered = "".join(path.read_text() for path in records)
    assert "password" not in rendered
    assert "mongodb://" not in rendered


def test_browser_creation_marks_and_updates_e2e_documents(tmp_path):
    run_id = f"markers-{uuid4().hex[:10]}"
    app = create_app(e2e_config(tmp_path, run_id))
    connections = app.extensions["roastlogger_databases"]
    client = app.test_client()
    beans = connections.local_db.beans
    roasts = connections.local_db.roasts
    query = {"test_data": True, "test_run_id": run_id}
    try:
        bean_name = f"E2E Bean {run_id}"
        response = client.post(
            "/api/beans/add",
            data={"name": bean_name, "stock_grams": "500"},
        )
        assert response.status_code == 302
        bean = beans.find_one({"name": bean_name})
        assert bean["test_data"] is True
        assert bean["test_run_id"] == run_id

        response = client.post(
            f"/api/beans/edit/{bean['_id']}",
            data={
                "name": f"{bean_name} Updated",
                "stock_grams": "450",
                "origin": "E2E Origin",
            },
        )
        assert response.status_code == 302
        updated_bean = beans.find_one({"_id": bean["_id"]})
        assert updated_bean["test_run_id"] == run_id

        response = client.post("/api/roast/create")
        roast_id = ObjectId(response.json["new_roast_id"])
        roast = roasts.find_one({"_id": roast_id})
        assert roast["test_data"] is True
        assert roast["test_run_id"] == run_id

        client.post(
            f"/api/roast/update_title/{roast_id}",
            json={"title": "Updated E2E Roast"},
        )
        updated_roast = roasts.find_one({"_id": roast_id})
        assert updated_roast["test_run_id"] == run_id
    finally:
        roasts.delete_many(query)
        beans.delete_many(query)
        connections.local_client.close()


def test_cleanup_removes_only_selected_run_and_its_logs(tmp_path):
    client = MongoClient("mongodb://127.0.0.1:27017/")
    database = client[E2E_DATABASE_NAME]
    run_id = f"cleanup-{uuid4().hex[:10]}"
    other_run = f"other-{uuid4().hex[:10]}"
    selected_roast_id = ObjectId()
    other_roast_id = ObjectId()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    try:
        database.roasts.insert_many(
            [
                {
                    "_id": selected_roast_id,
                    "test_data": True,
                    "test_run_id": run_id,
                },
                {
                    "_id": other_roast_id,
                    "test_data": True,
                    "test_run_id": other_run,
                },
            ]
        )
        database.beans.insert_many(
            [
                {
                    "_id": ObjectId(),
                    "test_data": True,
                    "test_run_id": run_id,
                },
                {
                    "_id": ObjectId(),
                    "test_data": True,
                    "test_run_id": other_run,
                },
            ]
        )
        for suffix in (".csv", "_sensor_diagnostics.csv"):
            (log_dir / f"{selected_roast_id}{suffix}").write_text("test")
            (log_dir / f"{other_roast_id}{suffix}").write_text("keep")

        result = cleanup_run(database, run_id, log_dir)

        assert result["roasts_deleted"] == 1
        assert result["beans_deleted"] == 1
        assert result["temp_logs_deleted"] == 2
        assert database.roasts.count_documents(
            {"test_run_id": other_run}
        ) == 1
        assert database.beans.count_documents(
            {"test_run_id": other_run}
        ) == 1
        assert (log_dir / f"{other_roast_id}.csv").exists()
    finally:
        database.roasts.delete_many(
            {"test_run_id": {"$in": [run_id, other_run]}}
        )
        database.beans.delete_many(
            {"test_run_id": {"$in": [run_id, other_run]}}
        )
        client.close()


def test_cleanup_and_start_refuse_non_e2e_database(tmp_path):
    class WrongDatabase:
        name = "roastlogger"

    with pytest.raises(CleanupSafetyError):
        cleanup_run(WrongDatabase(), "safe-run", tmp_path)
    with pytest.raises(ValueError, match=E2E_DATABASE_NAME):
        start(
            Namespace(
                run_id="safe-run",
                database="roastlogger",
                app_port=5011,
                sensor_port=5012,
            )
        )
    assert not (Path("tests/e2e/artifacts") / "safe-run").exists()
