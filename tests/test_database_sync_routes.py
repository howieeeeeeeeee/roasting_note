"""Settings preflight audit and legacy sync route safety tests."""

import json
from datetime import datetime
from pathlib import Path

import pytest

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
        assert "Legacy one-request" in response.json["error"]

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
    assert first.json["apply_eligible"] is True
    assert first.json["backup_confirmation"] == (
        f"BACKUP {first.json['run_id']}"
    )
    assert first.json["run_id"] != second.json["run_id"]
    records = list((tmp_path / "docs").rglob("*.json"))
    assert len(records) == 2
    assert all(path.name.endswith("__preflight.json") for path in records)
    assert first.json["plan"]["audit_path"] != str(records[0])
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
        lambda *args, **kwargs: {
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

    assert "if (syncRequestActive || syncRunActive)" in function
    assert "setSyncPreviewButtons(true, true)" in function
    assert "setSyncPreviewButtons(false)" in function
    assert "`/api/sync/preflight/${direction}`" in function
    assert "onlineButton.disabled = disabled" in template
    assert "localButton.disabled = disabled" in template


def test_loopback_json_same_origin_flow_requires_both_exact_tokens(tmp_path):
    app, connections = make_app(tmp_path)
    source = connections.online_db["beans"]
    source.documents["source-bean"] = {
        "_id": "source-bean",
        "archived": False,
        "updated_at": datetime(2026, 8, 20),
    }
    client = app.test_client()
    preflight = client.post("/api/sync/preflight/online-to-local")
    run_id = preflight.json["run_id"]
    direction = "online-to-local"

    backup = client.post(
        f"/api/sync/runs/{run_id}/backup",
        json={
            "direction": direction,
            "confirmation": f"BACKUP {run_id}",
        },
        headers={"Origin": "http://localhost"},
    )

    assert backup.status_code == 200
    assert backup.json["stage"] == "awaiting_apply"
    assert connections.local_db["beans"].write_count == 0
    active = client.get("/api/sync/runs/active")
    assert active.json["active"]["run_id"] == run_id

    wrong = client.post(
        f"/api/sync/runs/{run_id}/apply",
        json={"direction": direction, "confirmation": "wrong"},
    )
    assert wrong.status_code == 400
    assert connections.local_db["beans"].write_count == 0

    applied = client.post(
        f"/api/sync/runs/{run_id}/apply",
        json={
            "direction": direction,
            "confirmation": f"APPLY {direction} {run_id}",
        },
    )
    assert applied.status_code == 200
    assert applied.json["status"] == "success"
    assert connections.local_db["beans"].write_count == 1
    assert client.get("/api/sync/runs/active").json["active"] is None
    records = list((tmp_path / "docs").rglob("*.json"))
    assert len(records) == 2
    assert sum(path.name.endswith("__preflight.json") for path in records) == 1


def test_phase_guards_fail_before_state_backup_or_database_access(tmp_path):
    app, connections = make_app(tmp_path)
    client = app.test_client()
    preflight = client.post("/api/sync/preflight/online-to-local")
    run_id = preflight.json["run_id"]
    route = f"/api/sync/runs/{run_id}/backup"
    payload = {
        "direction": "online-to-local",
        "confirmation": f"BACKUP {run_id}",
    }

    remote = client.post(
        route,
        json=payload,
        environ_overrides={"REMOTE_ADDR": "192.0.2.10"},
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    nonlocal_host = client.post(
        route,
        json=payload,
        base_url="http://192.0.2.20",
    )
    cross_origin = client.post(
        route,
        json=payload,
        headers={"Origin": "https://attacker.example"},
    )
    userinfo_host = client.post(
        route,
        json=payload,
        headers={"Host": "attacker@127.0.0.1"},
    )
    userinfo_origin = client.post(
        route,
        json=payload,
        headers={"Origin": "http://attacker@localhost"},
    )
    queried_origin = client.post(
        route,
        json=payload,
        headers={"Origin": "http://localhost?trusted=false"},
    )
    non_json = client.post(route, data=json.dumps(payload))

    assert remote.status_code == 403
    assert nonlocal_host.status_code == 403
    assert cross_origin.status_code == 403
    assert userinfo_host.status_code == 403
    assert userinfo_origin.status_code == 403
    assert queried_origin.status_code == 403
    assert non_json.status_code == 415
    assert not (tmp_path / "db_backup").exists()
    assert len(list((tmp_path / "docs").rglob("*.json"))) == 1
    assert all(
        collection.write_count == 0
        for database in (connections.online_db, connections.local_db)
        for collection in database.collections.values()
    )


def test_nonloopback_preflight_stays_audited_and_preview_only(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/sync/preflight/online-to-local",
        environ_overrides={"REMOTE_ADDR": "192.0.2.30"},
        base_url="https://roastlogger.example",
    )

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["apply_eligible"] is False
    assert "backup_confirmation" not in response.json
    assert Path(tmp_path, response.json["audit_path"]).is_file()


def test_wrong_first_token_requires_fresh_preview_without_state(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()
    preflight = client.post("/api/sync/preflight/local-to-online")
    run_id = preflight.json["run_id"]
    route = f"/api/sync/runs/{run_id}/backup"

    wrong = client.post(
        route,
        json={"direction": "local-to-online", "confirmation": "wrong"},
    )
    retry = client.post(
        route,
        json={
            "direction": "local-to-online",
            "confirmation": f"BACKUP {run_id}",
        },
    )

    assert wrong.status_code == 400
    assert retry.status_code == 409
    assert "fresh preview" in retry.json["error"]
    assert not (tmp_path / "db_backup").exists()


@pytest.mark.parametrize("corruption", ["claim", "state", "config"])
def test_recovery_failures_keep_settings_sync_blocked(tmp_path, corruption):
    app, connections = make_app(tmp_path)
    client = app.test_client()
    preflight = client.post("/api/sync/preflight/online-to-local")
    run_id = preflight.json["run_id"]
    backup = client.post(
        f"/api/sync/runs/{run_id}/backup",
        json={
            "direction": "online-to-local",
            "confirmation": f"BACKUP {run_id}",
        },
    )
    assert backup.status_code == 200
    claim_path = (
        tmp_path / "db_backup/database_mirrors/browser_runs/active.json"
    )
    claim = json.loads(claim_path.read_text())
    if corruption == "claim":
        claim_path.write_text("{\n", encoding="utf-8")
    elif corruption == "state":
        Path(tmp_path, claim["state_path"]).write_text("{\n", encoding="utf-8")
    else:
        app.config["DEVICE"] = "changed-device"

    response = client.get("/api/sync/runs/active")

    assert response.status_code == 409
    assert response.json["stage"] == "recovery_required"
    assert all(
        collection.write_count == 0
        for database in (connections.online_db, connections.local_db)
        for collection in database.collections.values()
    )
    template = Path("templates/base.html").read_text(encoding="utf-8")
    assert "data.stage !== 'recovery_required'" in template
    assert "syncRunActive = true" in template
    assert "setSyncPreviewButtons(true)" in template
