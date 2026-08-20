"""Persistent phased Settings sync service safety tests."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest
from bson.objectid import ObjectId

from roastlogger.services.database_sync_plan import SyncRuntime, build_preflight
from roastlogger.services.database_sync_web import (
    PreviewRegistry,
    WebSyncConflict,
    WebSyncError,
    WebSyncRecoveryRequired,
    WebSyncService,
)
from roastlogger.services.database_sync_runner import SyncExecutionError
from tests.sync_fakes import (
    FakeClient,
    FakeCollection,
    FakeConnections,
    FakeDatabase,
)


VALUES = {
    "DEVICE": "web-test-mac",
    "MONGO_URI": "mongodb://online.example/roastlogger",
    "MONGO_URI_LOCAL": "mongodb://localhost:27017/roastlogger",
    "ONLINE_DB_NAME": "roastlogger",
    "LOCAL_DB_NAME": "roastlogger",
}


def _document():
    return {
        "_id": ObjectId(),
        "archived": False,
        "updated_at": datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
    }


def make_context(
    tmp_path,
    direction="online-to-local",
    *,
    backup=None,
    synchronize=None,
):
    online = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection(
                        [_document()] if direction == "online-to-local" else []
                    ),
                    "roasts": FakeCollection(),
                }
            )
        }
    )
    local = FakeClient(
        {
            "roastlogger": FakeDatabase(
                {
                    "beans": FakeCollection(
                        [_document()] if direction == "local-to-online" else []
                    ),
                    "roasts": FakeCollection(),
                }
            )
        }
    )
    connections = FakeConnections(online, local)
    runtime = SyncRuntime.from_mapping(VALUES, direction=direction)
    source = online if runtime.source_role == "online" else local
    destination = online if runtime.destination_role == "online" else local
    previews = PreviewRegistry()
    kwargs = {}
    if backup is not None:
        kwargs["backup"] = backup
    else:
        from roastlogger.services.database_backup import (
            backup_destination_database,
        )

        kwargs["backup"] = backup_destination_database
    if synchronize is not None:
        kwargs["synchronize"] = synchronize
    service = WebSyncService(
        VALUES,
        connections,
        tmp_path,
        previews,
        **kwargs,
    )
    return service, previews, runtime, source, destination, connections


def register_plan(service, runtime, source, destination, tmp_path, run_id):
    plan = build_preflight(
        runtime,
        source,
        destination,
        tmp_path,
        run_id=run_id,
    )
    service.register_preview(plan)
    return plan


@pytest.mark.parametrize(
    ("direction", "run_id"),
    [
        ("online-to-local", "20260820T120000Z-11111111"),
        ("local-to-online", "20260820T120100Z-22222222"),
    ],
)
def test_backup_resume_and_apply_preserve_both_directions(
    tmp_path,
    direction,
    run_id,
):
    service, _, runtime, source, destination, connections = make_context(
        tmp_path, direction
    )
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    destination_collection = destination["roastlogger"]["beans"]

    backed_up = service.backup(run_id, direction, f"BACKUP {run_id}")

    assert backed_up["stage"] == "awaiting_apply"
    assert backed_up["backup"]["status"] == "complete"
    assert destination_collection.write_count == 0
    state_files = list(tmp_path.rglob("*__browser-state.json"))
    assert len(state_files) == 1
    assert "mongodb://" not in state_files[0].read_text()

    restarted = WebSyncService(
        VALUES,
        connections,
        tmp_path,
        PreviewRegistry(),
        backup=lambda *_args: pytest.fail("resume repeated backup"),
    )
    active = restarted.active()
    assert active["restored"] is True
    assert active["run_id"] == run_id

    applied = restarted.apply(
        run_id,
        direction,
        f"APPLY {direction} {run_id}",
    )

    assert applied["status"] == "success"
    assert applied["sync"]["aggregate"]["added"] == 1
    assert destination_collection.write_count == 1
    assert restarted.active() is None
    assert len(list((tmp_path / "docs").rglob("*.json"))) == 1


def test_pre_backup_capability_does_not_survive_process_restart(tmp_path):
    service, _, runtime, source, destination, connections = make_context(tmp_path)
    run_id = "20260820T121000Z-33333333"
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    restarted = WebSyncService(
        VALUES,
        connections,
        tmp_path,
        PreviewRegistry(),
        backup=lambda *_args: pytest.fail("lost preview started backup"),
    )

    with pytest.raises(WebSyncConflict, match="fresh preview"):
        restarted.backup(run_id, runtime.direction, f"BACKUP {run_id}")

    assert not (tmp_path / "db_backup").exists()
    assert not (tmp_path / "docs").exists()


def test_wrong_backup_token_consumes_preview_without_activity(tmp_path):
    service, _, runtime, source, destination, _ = make_context(tmp_path)
    run_id = "20260820T122000Z-44444444"
    register_plan(service, runtime, source, destination, tmp_path, run_id)

    with pytest.raises(Exception, match="fresh preview"):
        service.backup(run_id, runtime.direction, "wrong")
    with pytest.raises(WebSyncConflict, match="fresh preview"):
        service.backup(run_id, runtime.direction, f"BACKUP {run_id}")

    assert not (tmp_path / "db_backup").exists()
    assert not (tmp_path / "docs").exists()
    assert destination["roastlogger"]["beans"].write_count == 0


def test_second_preview_loses_active_claim_and_requires_fresh_preview(tmp_path):
    service, _, runtime, source, destination, _ = make_context(tmp_path)
    first_id = "20260820T123000Z-55555555"
    second_id = "20260820T123100Z-66666666"
    register_plan(service, runtime, source, destination, tmp_path, first_id)
    register_plan(service, runtime, source, destination, tmp_path, second_id)

    service.backup(first_id, runtime.direction, f"BACKUP {first_id}")
    with pytest.raises(WebSyncConflict, match=first_id):
        service.backup(second_id, runtime.direction, f"BACKUP {second_id}")
    assert service.active()["run_id"] == first_id

    cancelled = service.cancel(first_id, runtime.direction)
    assert cancelled["status"] == "cancelled_after_backup"
    with pytest.raises(WebSyncConflict, match="fresh preview"):
        service.backup(
            second_id,
            runtime.direction,
            f"BACKUP {second_id}",
        )


def test_concurrent_wrong_and_correct_backup_attempts_are_one_use(tmp_path):
    service, previews, runtime, source, destination, _ = make_context(tmp_path)
    run_id = "20260820T123500Z-eeeeeeee"
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    original_take = previews.take
    wrong_took_preview = threading.Event()
    correct_finished_take = threading.Event()

    def coordinated_take(candidate, direction):
        if threading.current_thread().name == "wrong-backup":
            plan = original_take(candidate, direction)
            wrong_took_preview.set()
            assert correct_finished_take.wait(timeout=5)
            return plan
        assert wrong_took_preview.wait(timeout=5)
        try:
            return original_take(candidate, direction)
        finally:
            correct_finished_take.set()

    previews.take = coordinated_take
    outcomes = []

    def backup(confirmation):
        try:
            outcomes.append(
                service.backup(run_id, runtime.direction, confirmation)
            )
        except Exception as error:
            outcomes.append(error)

    threads = [
        threading.Thread(target=backup, args=("wrong",), name="wrong-backup"),
        threading.Thread(
            target=backup,
            args=(f"BACKUP {run_id}",),
            name="correct-backup",
        ),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert len(outcomes) == 2
    assert sum(isinstance(item, WebSyncConflict) for item in outcomes) == 1
    assert sum(
        isinstance(item, WebSyncError)
        and "confirmation did not match" in str(item)
        for item in outcomes
    ) == 1
    assert not (tmp_path / "db_backup").exists()
    assert not (tmp_path / "docs").exists()


def test_wrong_apply_token_leaves_verified_run_available_to_cancel(tmp_path):
    service, _, runtime, source, destination, _ = make_context(tmp_path)
    run_id = "20260820T124000Z-77777777"
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    service.backup(run_id, runtime.direction, f"BACKUP {run_id}")

    with pytest.raises(Exception, match="apply confirmation"):
        service.apply(run_id, runtime.direction, "wrong")

    assert service.active()["run_id"] == run_id
    terminal = service.cancel(run_id, runtime.direction)
    assert terminal["status"] == "cancelled_after_backup"
    assert destination["roastlogger"]["beans"].write_count == 0
    audit = json.loads(Path(tmp_path, terminal["audit_path"]).read_text())
    assert audit["status"] == "cancelled_after_backup"
    with pytest.raises(WebSyncConflict, match="not active"):
        service.cancel(run_id, runtime.direction)


def test_corrupt_backup_blocks_apply_and_preserves_active_claim(tmp_path):
    service, _, runtime, source, destination, _ = make_context(tmp_path)
    run_id = "20260820T125000Z-88888888"
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    backed_up = service.backup(run_id, runtime.direction, f"BACKUP {run_id}")
    manifest = tmp_path / backed_up["backup"]["path"] / "manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")

    with pytest.raises(WebSyncRecoveryRequired, match="verification failed"):
        service.apply(
            run_id,
            runtime.direction,
            f"APPLY {runtime.direction} {run_id}",
        )

    assert destination["roastlogger"]["beans"].write_count == 0
    claim = json.loads(
        (tmp_path / "db_backup/database_mirrors/browser_runs/active.json")
        .read_text()
    )
    assert claim["run_id"] == run_id


@pytest.mark.parametrize(
    ("direction", "setting", "changed_uri"),
    [
        (
            "local-to-online",
            "MONGO_URI",
            "mongodb+srv://online.example/roastlogger",
        ),
        (
            "online-to-local",
            "MONGO_URI",
            "mongodb://online.example/roastlogger?replicaSet=changed",
        ),
        (
            "online-to-local",
            "MONGO_URI_LOCAL",
            "mongodb://localhost:27017/roastlogger?directConnection=true",
        ),
    ],
)
def test_restart_rejects_endpoint_drift_before_apply(
    tmp_path,
    direction,
    setting,
    changed_uri,
):
    service, _, runtime, source, destination, connections = make_context(
        tmp_path,
        direction,
    )
    run_id = "20260820T125200Z-abcdef12"
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    service.backup(run_id, direction, f"BACKUP {run_id}")
    changed_values = {**VALUES, setting: changed_uri}
    restarted = WebSyncService(
        changed_values,
        connections,
        tmp_path,
        PreviewRegistry(),
        backup=lambda *_args: pytest.fail("config drift repeated backup"),
    )

    with pytest.raises(WebSyncRecoveryRequired, match="configuration"):
        restarted.apply(run_id, direction, f"APPLY {direction} {run_id}")

    assert destination["roastlogger"]["beans"].write_count == 0


def test_interrupted_terminal_transition_requires_manual_recovery(tmp_path):
    service, _, runtime, source, destination, _ = make_context(tmp_path)
    run_id = "20260820T125500Z-dddddddd"
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    service.backup(run_id, runtime.direction, f"BACKUP {run_id}")
    state = service.store.read_active()
    service.store.begin_transition(state, "apply")

    with pytest.raises(WebSyncRecoveryRequired, match="interrupted terminal"):
        service.active()

    assert destination["roastlogger"]["beans"].write_count == 0
    assert not (tmp_path / "docs").exists()


def test_backup_failure_writes_terminal_audit_and_releases_claim(tmp_path):
    def failed_backup(*_args):
        raise RuntimeError("credential-bearing backup failure")

    service, _, runtime, source, destination, _ = make_context(
        tmp_path, backup=failed_backup
    )
    run_id = "20260820T130000Z-99999999"
    register_plan(service, runtime, source, destination, tmp_path, run_id)

    result = service.backup(run_id, runtime.direction, f"BACKUP {run_id}")

    assert result["status"] == "backup_failed"
    assert result["success"] is False
    assert service.active() is None
    audit = Path(tmp_path, result["audit_path"]).read_text()
    assert "credential-bearing" not in audit
    assert "mongodb://" not in audit


def test_partial_sync_failure_is_terminal_and_cannot_replay(tmp_path):
    completed = {
        "beans": {
            "added": 1,
            "updated": 0,
            "skipped": 0,
            "conflicts": 0,
            "post_run_count": 1,
        }
    }

    def failed_sync(*_args):
        raise SyncExecutionError(
            "roasts",
            completed,
            RuntimeError("credential-bearing sync failure"),
        )

    service, _, runtime, source, destination, _ = make_context(
        tmp_path,
        synchronize=failed_sync,
    )
    run_id = "20260820T131000Z-aaaaaaaa"
    register_plan(service, runtime, source, destination, tmp_path, run_id)
    service.backup(run_id, runtime.direction, f"BACKUP {run_id}")

    result = service.apply(
        run_id,
        runtime.direction,
        f"APPLY {runtime.direction} {run_id}",
    )

    assert result["status"] == "partial_sync_failed"
    assert result["sync"]["failed_collection"] == "roasts"
    assert result["sync"]["collections"] == completed
    assert service.active() is None
    with pytest.raises(WebSyncConflict, match="not active"):
        service.apply(
            run_id,
            runtime.direction,
            f"APPLY {runtime.direction} {run_id}",
        )


def _gated_first_backup_verification(service, barrier):
    original = service._verify_backup
    calls = 0

    def verify(state, runtime):
        nonlocal calls
        result = original(state, runtime)
        calls += 1
        if calls == 1:
            barrier.wait(timeout=5)
        return result

    service._verify_backup = verify


def _successful_sync(counter, lock):
    def synchronize(*_args):
        with lock:
            counter["calls"] += 1
        return {
            "collections": {},
            "aggregate": {
                "added": 0,
                "updated": 0,
                "skipped": 0,
                "conflicts": 0,
            },
            "verified": True,
        }

    return synchronize


def test_simultaneous_apply_requests_execute_once_and_write_one_audit(tmp_path):
    counter = {"calls": 0}
    lock = threading.Lock()
    synchronize = _successful_sync(counter, lock)
    first, _, runtime, source, destination, connections = make_context(
        tmp_path,
        synchronize=synchronize,
    )
    run_id = "20260820T132000Z-bbbbbbbb"
    register_plan(first, runtime, source, destination, tmp_path, run_id)
    first.backup(run_id, runtime.direction, f"BACKUP {run_id}")
    second = WebSyncService(
        VALUES,
        connections,
        tmp_path,
        PreviewRegistry(),
        backup=lambda *_args: pytest.fail("concurrent apply repeated backup"),
        synchronize=synchronize,
    )
    barrier = threading.Barrier(2)
    _gated_first_backup_verification(first, barrier)
    _gated_first_backup_verification(second, barrier)
    outcomes = []

    def apply(service):
        try:
            outcomes.append(
                service.apply(
                    run_id,
                    runtime.direction,
                    f"APPLY {runtime.direction} {run_id}",
                )
            )
        except Exception as error:
            outcomes.append(error)

    threads = [
        threading.Thread(target=apply, args=(first,)),
        threading.Thread(target=apply, args=(second,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert counter["calls"] == 1
    assert sum(isinstance(item, dict) for item in outcomes) == 1
    assert sum(isinstance(item, WebSyncConflict) for item in outcomes) == 1
    assert len(list((tmp_path / "docs").rglob("*.json"))) == 1
    assert first.active() is None


def test_simultaneous_apply_and_cancel_have_one_terminal_owner(tmp_path):
    counter = {"calls": 0}
    lock = threading.Lock()
    synchronize = _successful_sync(counter, lock)
    apply_service, _, runtime, source, destination, connections = make_context(
        tmp_path,
        synchronize=synchronize,
    )
    run_id = "20260820T133000Z-cccccccc"
    register_plan(
        apply_service,
        runtime,
        source,
        destination,
        tmp_path,
        run_id,
    )
    apply_service.backup(run_id, runtime.direction, f"BACKUP {run_id}")
    cancel_service = WebSyncService(
        VALUES,
        connections,
        tmp_path,
        PreviewRegistry(),
        backup=lambda *_args: pytest.fail("concurrent cancel repeated backup"),
        synchronize=synchronize,
    )
    barrier = threading.Barrier(2)
    _gated_first_backup_verification(apply_service, barrier)
    _gated_first_backup_verification(cancel_service, barrier)
    outcomes = []

    def apply():
        try:
            outcomes.append(
                apply_service.apply(
                    run_id,
                    runtime.direction,
                    f"APPLY {runtime.direction} {run_id}",
                )
            )
        except Exception as error:
            outcomes.append(error)

    def cancel():
        try:
            outcomes.append(cancel_service.cancel(run_id, runtime.direction))
        except Exception as error:
            outcomes.append(error)

    threads = [threading.Thread(target=apply), threading.Thread(target=cancel)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    terminals = [item for item in outcomes if isinstance(item, dict)]
    assert len(terminals) == 1
    assert terminals[0]["status"] in {"success", "cancelled_after_backup"}
    assert counter["calls"] == (1 if terminals[0]["status"] == "success" else 0)
    assert sum(isinstance(item, WebSyncConflict) for item in outcomes) == 1
    assert len(list((tmp_path / "docs").rglob("*.json"))) == 1
    assert apply_service.active() is None
