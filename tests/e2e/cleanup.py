"""Run-scoped E2E database and temperature-log cleanup."""

from __future__ import annotations

from pathlib import Path

from roastlogger.e2e import E2E_DATABASE_NAME, validate_run_id


class CleanupSafetyError(ValueError):
    """Cleanup was asked to operate outside the dedicated E2E scope."""


def cleanup_run(database, run_id: str, log_dir: Path) -> dict:
    run_id = validate_run_id(run_id)
    if database.name != E2E_DATABASE_NAME:
        raise CleanupSafetyError(
            f"cleanup requires database {E2E_DATABASE_NAME}"
        )
    query = {"test_data": True, "test_run_id": run_id}
    roast_ids = [
        str(document["_id"])
        for document in database.roasts.find(query, {"_id": 1})
    ]

    roasts_deleted = database.roasts.delete_many(query).deleted_count
    beans_deleted = database.beans.delete_many(query).deleted_count
    logs_deleted = 0
    for roast_id in roast_ids:
        for suffix in (".csv", "_sensor_diagnostics.csv"):
            path = Path(log_dir) / f"{roast_id}{suffix}"
            if path.is_file():
                path.unlink()
                logs_deleted += 1

    remaining_roasts = database.roasts.count_documents(query)
    remaining_beans = database.beans.count_documents(query)
    if remaining_roasts or remaining_beans:
        raise CleanupSafetyError("run-scoped cleanup verification failed")
    return {
        "run_id": run_id,
        "roasts_deleted": roasts_deleted,
        "beans_deleted": beans_deleted,
        "temp_logs_deleted": logs_deleted,
        "remaining_roasts": remaining_roasts,
        "remaining_beans": remaining_beans,
    }
