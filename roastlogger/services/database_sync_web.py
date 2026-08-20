"""Persistent guarded Settings workflow for local database sync."""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from copy import deepcopy
from pathlib import Path

from roastlogger.services.database_backup import verify_backup_result
from roastlogger.services.database_sync_plan import (
    DIRECTIONS,
    SyncRuntime,
    planned_audit_path,
    planned_backup_path,
)
from roastlogger.services.database_sync_runner import (
    begin_guarded_execution,
    perform_apply_phase,
    perform_backup_phase,
    perform_cancel_phase,
    synchronize_collections,
)


RUN_ID_PATTERN = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{8}")
NONTERMINAL_STAGES = {
    "backup_in_progress",
    "awaiting_apply",
    "apply_in_progress",
    "cancel_in_progress",
}


class WebSyncError(RuntimeError):
    status_code = 400

    def __init__(self, message, *, run_id=None, stage=None):
        super().__init__(message)
        self.run_id = run_id
        self.stage = stage


class WebSyncConflict(WebSyncError):
    status_code = 409


class WebSyncRecoveryRequired(WebSyncConflict):
    def __init__(self, message, *, run_id=None, stage="recovery_required"):
        super().__init__(message, run_id=run_id, stage=stage)


def validate_web_run_id(run_id) -> str:
    value = str(run_id or "")
    if not RUN_ID_PATTERN.fullmatch(value):
        raise WebSyncError("run ID is invalid; start a fresh preview")
    return value


def validate_web_direction(direction) -> str:
    if direction not in DIRECTIONS:
        raise WebSyncError("sync direction is invalid")
    return direction


def _write_json_file(path: Path, value: dict, *, exclusive: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    try:
        with temporary.open("x", encoding="utf-8") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        if exclusive:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_json_file(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise WebSyncRecoveryRequired(
            "saved sync state is unreadable; inspect the ignored run artifacts"
        ) from error
    if not isinstance(value, dict):
        raise WebSyncRecoveryRequired(
            "saved sync state is invalid; inspect the ignored run artifacts"
        )
    return value


class PreviewRegistry:
    """One-process, one-use capabilities for the pre-backup transition."""

    def __init__(self):
        self._items = {}
        self._lock = threading.Lock()

    def register(self, plan: dict) -> None:
        with self._lock:
            self._items[plan["run_id"]] = deepcopy(plan)

    def take(self, run_id: str, direction: str) -> dict:
        with self._lock:
            plan = self._items.get(run_id)
            if plan is None or plan.get("direction") != direction:
                raise WebSyncConflict(
                    "preview capability is unavailable; start a fresh preview",
                    run_id=run_id,
                )
            self._items.pop(run_id, None)
            return deepcopy(plan)


class BrowserRunStore:
    """Atomic single-active-run state stored under the ignored backup root."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.mirror_root = (
            self.root / "db_backup" / "database_mirrors"
        ).resolve()
        self.claim_path = self.mirror_root / "browser_runs" / "active.json"

    def _state_path(self, state: dict) -> Path:
        backup_path = Path(state["plan"]["backup"]["path"]).resolve()
        if not backup_path.is_relative_to(self.mirror_root):
            raise WebSyncRecoveryRequired("saved backup path is outside its root")
        return backup_path.with_name(f"{backup_path.name}__browser-state.json")

    def _transition_path(self, state: dict) -> Path:
        state_path = self._state_path(state)
        return state_path.with_name(
            state_path.name.replace("__browser-state.json", "__transition.json")
        )

    def claim(self, state: dict) -> None:
        state_path = self._state_path(state)
        claim = {
            "schema_version": 1,
            "run_id": state["run_id"],
            "direction": state["direction"],
            "state_path": str(state_path.relative_to(self.root)),
        }
        try:
            _write_json_file(state_path, state, exclusive=True)
        except FileExistsError as error:
            raise WebSyncConflict(
                "this preview has already entered the guarded workflow",
                run_id=state["run_id"],
            ) from error
        try:
            _write_json_file(self.claim_path, claim, exclusive=True)
        except FileExistsError as error:
            state_path.unlink(missing_ok=True)
            active_run = "another run"
            try:
                active_run = _read_json_file(self.claim_path).get(
                    "run_id", active_run
                )
            except WebSyncRecoveryRequired:
                pass
            raise WebSyncConflict(
                f"sync run {active_run} must finish or be recovered first",
                run_id=state["run_id"],
            ) from error
        except Exception:
            state_path.unlink(missing_ok=True)
            raise

    def _read_claim(self) -> dict | None:
        if not self.claim_path.exists():
            return None
        claim = _read_json_file(self.claim_path)
        if claim.get("schema_version") != 1:
            raise WebSyncRecoveryRequired(
                "active sync claim schema is unsupported"
            )
        try:
            run_id = validate_web_run_id(claim.get("run_id"))
            direction = validate_web_direction(claim.get("direction"))
            state_path = (self.root / claim["state_path"]).resolve()
        except (KeyError, WebSyncError) as error:
            raise WebSyncRecoveryRequired(
                "active sync claim is corrupt; inspect ignored run artifacts"
            ) from error
        if not state_path.is_relative_to(self.mirror_root):
            raise WebSyncRecoveryRequired("active sync state path is unsafe")
        return {
            **claim,
            "run_id": run_id,
            "direction": direction,
            "resolved_state_path": state_path,
        }

    def read_active(self) -> dict | None:
        claim = self._read_claim()
        if claim is None:
            return None
        state = _read_json_file(claim["resolved_state_path"])
        if (
            state.get("schema_version") != 1
            or state.get("run_id") != claim["run_id"]
            or state.get("direction") != claim["direction"]
            or state.get("stage") not in NONTERMINAL_STAGES
            or self._state_path(state) != claim["resolved_state_path"]
        ):
            raise WebSyncRecoveryRequired(
                "active sync state is inconsistent; inspect ignored run artifacts",
                run_id=claim["run_id"],
            )
        transition_path = self._transition_path(state)
        if transition_path.exists():
            raise WebSyncRecoveryRequired(
                "an interrupted terminal transition requires artifact review",
                run_id=claim["run_id"],
                stage="recovery_required",
            )
        return state

    def begin_transition(self, state: dict, transition: str) -> None:
        if transition not in {"apply", "cancel"}:
            raise ValueError("unknown sync transition")
        claim = self._read_claim()
        if (
            claim is None
            or claim["run_id"] != state.get("run_id")
            or state.get("stage") != "awaiting_apply"
        ):
            raise WebSyncConflict("the sync run cannot enter this transition")
        marker = {
            "schema_version": 1,
            "run_id": state["run_id"],
            "direction": state["direction"],
            "transition": transition,
        }
        try:
            _write_json_file(
                self._transition_path(state),
                marker,
                exclusive=True,
            )
        except FileExistsError as error:
            raise WebSyncConflict(
                "another terminal action already owns this sync run",
                run_id=state["run_id"],
            ) from error

    def update(self, state: dict) -> None:
        claim = self._read_claim()
        if claim is None or claim["run_id"] != state.get("run_id"):
            raise WebSyncRecoveryRequired(
                "active sync ownership was lost; inspect ignored run artifacts",
                run_id=state.get("run_id"),
            )
        state_path = self._state_path(state)
        if state_path != claim["resolved_state_path"]:
            raise WebSyncRecoveryRequired("active sync state path changed")
        _write_json_file(state_path, state, exclusive=False)

    def release(self, state: dict) -> None:
        claim = self._read_claim()
        if claim is None or claim["run_id"] != state.get("run_id"):
            raise WebSyncRecoveryRequired(
                "terminal sync state could not release its active claim",
                run_id=state.get("run_id"),
            )
        self.claim_path.unlink()


def _runtime_snapshot(runtime: SyncRuntime) -> dict:
    return {
        "device": runtime.device,
        "direction": runtime.direction,
        "batch_size": runtime.batch_size,
        "requested_collections": list(runtime.requested_collections),
        "source": runtime.source_descriptor,
        "destination": runtime.destination_descriptor,
        "source_endpoint_fingerprint": runtime.source_endpoint_fingerprint,
        "destination_endpoint_fingerprint": (
            runtime.destination_endpoint_fingerprint
        ),
    }


class WebSyncService:
    """Coordinate server-owned preview, backup, resume, apply, and cancel."""

    def __init__(
        self,
        values,
        connections,
        root: Path,
        previews: PreviewRegistry,
        *,
        backup,
        synchronize=synchronize_collections,
    ):
        self.values = values
        self.connections = connections
        self.root = Path(root).resolve()
        self.previews = previews
        self.store = BrowserRunStore(self.root)
        self.backup_executor = backup
        self.sync_executor = synchronize

    def register_preview(self, plan: dict) -> None:
        self.previews.register(plan)

    def _runtime(self, direction: str) -> SyncRuntime:
        return SyncRuntime.from_mapping(self.values, direction=direction)

    def _clients(self, runtime: SyncRuntime):
        source = (
            self.connections.online_client
            if runtime.source_role == "online"
            else self.connections.local_client
        )
        destination = (
            self.connections.online_client
            if runtime.destination_role == "online"
            else self.connections.local_client
        )
        return source, destination

    def _verify_identity(self, state: dict, runtime: SyncRuntime) -> None:
        plan = state["plan"]
        expected_backup = planned_backup_path(
            self.root, runtime, state["run_id"]
        ).resolve()
        expected_audit = planned_audit_path(
            self.root, runtime, state["run_id"]
        ).resolve()
        try:
            identity_matches = (
                state["runtime"] == _runtime_snapshot(runtime)
                and plan["run_id"] == state["run_id"]
                and plan["direction"] == runtime.direction
                and plan["device"] == runtime.device
                and plan["batch_size"] == runtime.batch_size
                and plan["requested_collections"]
                == list(runtime.requested_collections)
                and plan["resolved_collections"]
                == list(runtime.requested_collections)
                and plan["source"] == runtime.source_descriptor
                and plan["destination"] == runtime.destination_descriptor
                and plan["backup"]["scope"]
                == "complete_destination_database"
                and Path(plan["backup"]["path"]).resolve() == expected_backup
                and Path(plan["audit_path"]).resolve() == expected_audit
            )
        except (KeyError, TypeError, OSError) as error:
            raise WebSyncRecoveryRequired(
                "saved sync identity is incomplete; inspect ignored run artifacts",
                run_id=state.get("run_id"),
            ) from error
        if not identity_matches:
            raise WebSyncRecoveryRequired(
                "saved sync identity no longer matches server configuration",
                run_id=state["run_id"],
            )
        record = state.get("record")
        backup = state.get("backup")
        if record is None:
            return
        record_matches = (
            record.get("schema_version") == 1
            and record.get("trigger") == "settings_ui"
            and record.get("run_id") == state["run_id"]
            and record.get("DEVICE") == runtime.device
            and record.get("direction") == runtime.direction
            and record.get("source") == runtime.source_descriptor
            and record.get("destination") == runtime.destination_descriptor
            and record.get("batch_size") == runtime.batch_size
            and record.get("requested_collections")
            == list(runtime.requested_collections)
            and record.get("resolved_collections")
            == list(runtime.requested_collections)
            and isinstance(record.get("started_at"), str)
            and (backup is None or record.get("backup") == backup)
        )
        if not record_matches:
            raise WebSyncRecoveryRequired(
                "saved sync audit state is inconsistent",
                run_id=state["run_id"],
            )

    def _verify_backup(self, state: dict, runtime: SyncRuntime) -> dict:
        try:
            return verify_backup_result(
                runtime,
                self.root,
                state["run_id"],
                state["backup"],
            )
        except Exception as error:
            raise WebSyncRecoveryRequired(
                "saved backup verification failed; do not apply this run",
                run_id=state["run_id"],
                stage="recovery_required",
            ) from error

    def _terminalize(self, state: dict, result: dict, record: dict) -> dict:
        state.update(
            {
                "stage": "terminal",
                "terminal_status": result["status"],
                "result": result,
                "record": record,
            }
        )
        self.store.update(state)
        self.store.release(state)
        return self._terminal_response(state)

    def backup(self, run_id, direction, confirmation) -> dict:
        run_id = validate_web_run_id(run_id)
        direction = validate_web_direction(direction)
        plan = self.previews.take(run_id, direction)
        if confirmation != f"BACKUP {run_id}":
            raise WebSyncError(
                "backup confirmation did not match; start a fresh preview",
                run_id=run_id,
            )
        runtime = self._runtime(direction)
        preview_state = {
            "run_id": run_id,
            "direction": direction,
            "runtime": _runtime_snapshot(runtime),
            "plan": plan,
        }
        self._verify_identity(preview_state, runtime)
        record = begin_guarded_execution(
            runtime,
            plan,
            trigger="settings_ui",
        )
        state = {
            "schema_version": 1,
            **preview_state,
            "stage": "backup_in_progress",
            "record": record,
            "backup": None,
        }
        self.store.claim(state)
        _, destination = self._clients(runtime)
        result, record = perform_backup_phase(
            runtime,
            destination,
            self.root,
            plan,
            record,
            backup=self.backup_executor,
            verify=verify_backup_result,
        )
        state["record"] = record
        if result["status"] != "awaiting_apply":
            return self._terminalize(state, result, record)
        state.update(
            {
                "stage": "awaiting_apply",
                "backup": result["backup"],
            }
        )
        self.store.update(state)
        return self._active_response(state)

    def active(self) -> dict | None:
        state = self.store.read_active()
        if state is None:
            return None
        if state["stage"] != "awaiting_apply":
            raise WebSyncRecoveryRequired(
                "an interrupted sync phase requires manual artifact review",
                run_id=state["run_id"],
                stage="recovery_required",
            )
        runtime = self._runtime(state["direction"])
        self._verify_identity(state, runtime)
        self._verify_backup(state, runtime)
        return self._active_response(state, restored=True)

    def apply(self, run_id, direction, confirmation) -> dict:
        run_id = validate_web_run_id(run_id)
        direction = validate_web_direction(direction)
        state = self.store.read_active()
        if state is None or state["run_id"] != run_id:
            raise WebSyncConflict("the requested sync run is not active")
        if state["direction"] != direction or state["stage"] != "awaiting_apply":
            raise WebSyncConflict("the sync run is not awaiting apply")
        if confirmation != f"APPLY {direction} {run_id}":
            raise WebSyncError("apply confirmation did not match", run_id=run_id)
        runtime = self._runtime(direction)
        self._verify_identity(state, runtime)
        self._verify_backup(state, runtime)
        self.store.begin_transition(state, "apply")
        self._verify_backup(state, runtime)
        state["stage"] = "apply_in_progress"
        self.store.update(state)
        source, destination = self._clients(runtime)
        result, record = perform_apply_phase(
            runtime,
            source,
            destination,
            self.root,
            state["plan"],
            state["record"],
            synchronize=self.sync_executor,
        )
        return self._terminalize(state, result, record)

    def cancel(self, run_id, direction) -> dict:
        run_id = validate_web_run_id(run_id)
        direction = validate_web_direction(direction)
        state = self.store.read_active()
        if state is None or state["run_id"] != run_id:
            raise WebSyncConflict("the requested sync run is not active")
        if state["direction"] != direction or state["stage"] != "awaiting_apply":
            raise WebSyncConflict("the sync run is not awaiting cancellation")
        runtime = self._runtime(direction)
        self._verify_identity(state, runtime)
        self._verify_backup(state, runtime)
        self.store.begin_transition(state, "cancel")
        self._verify_backup(state, runtime)
        state["stage"] = "cancel_in_progress"
        self.store.update(state)
        result, record = perform_cancel_phase(
            runtime,
            self.root,
            state["plan"],
            state["record"],
        )
        return self._terminalize(state, result, record)

    def _display_path(self, value):
        if not value:
            return None
        path = Path(value).resolve()
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return "unavailable"

    def _backup_summary(self, backup: dict) -> dict:
        return {
            "status": backup["status"],
            "collection_count": backup.get("collection_count", 0),
            "document_count": backup.get("document_count", 0),
            "manifest_sha256": backup.get("manifest_sha256"),
            "path": self._display_path(backup.get("path")),
        }

    def _active_response(self, state: dict, *, restored=False) -> dict:
        return {
            "success": True,
            "run_id": state["run_id"],
            "direction": state["direction"],
            "stage": "awaiting_apply",
            "restored": restored,
            "backup": self._backup_summary(state["backup"]),
            "apply_confirmation": (
                f"APPLY {state['direction']} {state['run_id']}"
            ),
        }

    def _terminal_response(self, state: dict) -> dict:
        result = state["result"]
        return {
            "success": result["status"]
            in {"success", "cancelled_after_backup"},
            "run_id": state["run_id"],
            "direction": state["direction"],
            "stage": "terminal",
            "status": result["status"],
            "backup": self._backup_summary(state["record"]["backup"]),
            "sync": result.get("sync"),
            "error": state["record"].get("failure"),
            "audit_path": self._display_path(result.get("audit_path")),
            "recovery_path": self._display_path(result.get("recovery_path")),
        }
