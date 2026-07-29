"""Fail-closed configuration and document markers for local E2E runs."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from urllib.parse import urlsplit

from flask import current_app


E2E_DATABASE_NAME = "roastlogger_e2e"
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


class E2EConfigError(ValueError):
    """An unsafe or incomplete E2E runtime configuration."""


def validate_run_id(run_id: str | None) -> str:
    value = (run_id or "").strip()
    if not value or not RUN_ID_PATTERN.fullmatch(value):
        raise E2EConfigError(
            "E2E_RUN_ID must use 1-64 letters, digits, underscores, or hyphens"
        )
    return value


def _require_loopback_url(value: str, label: str) -> None:
    parsed = urlsplit(value)
    if not parsed.hostname:
        raise E2EConfigError(f"{label} must include a loopback host")
    try:
        is_loopback = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        is_loopback = parsed.hostname == "localhost"
    if not is_loopback:
        raise E2EConfigError(f"{label} must use a loopback host")


def configure_e2e_runtime(config, repository_root: Path) -> None:
    if not config.get("E2E_MODE"):
        return
    if config.get("LOCAL_DB_NAME") != E2E_DATABASE_NAME:
        raise E2EConfigError(
            f"E2E mode requires LOCAL_DB_NAME={E2E_DATABASE_NAME}"
        )
    run_id = validate_run_id(config.get("E2E_RUN_ID"))
    _require_loopback_url(config["MONGO_URI_LOCAL"], "MONGO_URI_LOCAL")
    _require_loopback_url(config["TEMP_SENSOR_URL"], "TEMP_SENSOR_URL")

    artifact_root = config.get("E2E_ARTIFACT_ROOT")
    if not artifact_root:
        artifact_root = (
            repository_root / "tests" / "e2e" / "artifacts" / run_id
        )
    artifact_root = Path(artifact_root).resolve()
    config.update(
        {
            "DEFAULT_DB": "local",
            "E2E_RUN_ID": run_id,
            "E2E_ARTIFACT_ROOT": str(artifact_root),
            "TEMP_LOG_DIR": str(artifact_root / "temp_logs"),
        }
    )


def document_markers() -> dict:
    if not current_app.config.get("E2E_MODE"):
        return {}
    return {
        "test_data": True,
        "test_run_id": current_app.config["E2E_RUN_ID"],
    }
