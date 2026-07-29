"""Settings preflight audit and legacy sync route safety tests."""

import json
from pathlib import Path

from roastlogger import create_app
import roastlogger.blueprints.settings as settings_routes
from tests.sync_fakes import (
    FakeClient,
    FakeCollection,
    FakeConnections,
    FakeDatabase,
)


def make_app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DEVICE": "route-test-mac",
            "MONGO_URI": "mongodb://online.example/roastlogger",
            "MONGO_URI_LOCAL": "mongodb://localhost:27017/roastlogger",
            "REPOSITORY_ROOT": str(tmp_path),
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
    local = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection(),
                    "roasts": FakeCollection(),
                }
            )
        }
    )
    connections = FakeConnections(online, local)
    app.extensions["roastlogger_databases"] = connections
    return app, connections


def test_legacy_mutating_routes_fail_closed_without_database_access(tmp_path):
    app, connections = make_app(tmp_path)
    client = app.test_client()

    for direction in ("online-to-local", "local-to-online"):
        response = client.post(f"/api/sync/{direction}")
        assert response.status_code == 409
        assert response.json["success"] is False
        assert "CLI-only" in response.json["error"]

    assert all(
        collection.write_count == 0
        for database in (connections.online_db, connections.local_db)
        for collection in database.collections.values()
    )
    assert not (tmp_path / "docs").exists()
    assert not (tmp_path / "db_backup").exists()


def test_each_settings_preflight_click_writes_one_terminal_audit(tmp_path):
    app, connections = make_app(tmp_path)
    client = app.test_client()

    first = client.post("/api/sync/preflight/online-to-local")
    second = client.post("/api/sync/preflight/online-to-local")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json["success"] is True
    assert first.json["audit_recorded"] is True
    assert first.json["plan"]["backup"]["scope"] == (
        "complete_destination_database"
    )
    assert first.json["run_id"] != second.json["run_id"]
    records = list((tmp_path / "docs").rglob("*.json"))
    assert len(records) == 2
    record = json.loads(records[0].read_text())
    assert record["DEVICE"] == "route-test-mac"
    assert record["trigger"] == "settings_ui"
    assert record["event"] == "sync_button_clicked"
    assert record["preflight"]["status"] == "success"
    assert "mongodb://" not in json.dumps(record)
    assert all(
        collection.write_count == 0
        for database in (connections.online_db, connections.local_db)
        for collection in database.collections.values()
    )
    assert not (tmp_path / "db_backup").exists()


def test_failed_preflight_is_audited_without_leaking_driver_error(tmp_path):
    app, _ = make_app(tmp_path)
    app.extensions["roastlogger_databases"].online_client.admin.available = False
    response = app.test_client().post(
        "/api/sync/preflight/online-to-local"
    )

    assert response.status_code == 503
    assert response.json["audit_recorded"] is True
    assert response.json["error"] == {
        "type": "SyncSafetyError",
        "message": "online endpoint is unavailable",
    }
    audit = Path(tmp_path, response.json["audit_path"]).read_text()
    assert "credential-bearing" not in audit
    assert "mongodb://" not in audit


def test_audit_write_failure_is_prominent_and_returns_server_error(
    monkeypatch,
    tmp_path,
):
    app, _ = make_app(tmp_path)
    monkeypatch.setattr(
        settings_routes,
        "run_ui_preflight",
        lambda *args: {
            "success": False,
            "run_id": "20260729T140000Z-auditbad",
            "plan": None,
            "error": None,
            "audit_recorded": False,
            "audit_error": {
                "type": "OSError",
                "message": "database operation failed; inspect local diagnostics",
            },
        },
    )

    response = app.test_client().post(
        "/api/sync/preflight/online-to-local"
    )

    assert response.status_code == 500
    assert response.json["audit_recorded"] is False
    template = Path("templates/base.html").read_text(encoding="utf-8")
    assert "'Audit failure'" in template
    assert "preflight audit record was not persisted" in template


def test_settings_markup_prevents_overlapping_preflight_requests():
    template = Path("templates/base.html").read_text(encoding="utf-8")
    function = template.split("async function syncData(direction)", 1)[1]
    function = function.split("// Toast Notifications", 1)[0]

    assert "if (syncPreflightActive)" in function
    assert "setSyncPreflightButtons(true)" in function
    assert "setSyncPreflightButtons(false)" in function
    assert "`/api/sync/preflight/${direction}`" in function
    assert "onlineButton.disabled = disabled" in template
    assert "localButton.disabled = disabled" in template
