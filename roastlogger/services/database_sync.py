"""Timestamp-aware synchronization shared by route and operational adapters."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime

import pytz

from roastlogger.time_utils import get_current_time_with_tz


FORECAST_FIELDS = (
    "source_documents",
    "destination_documents",
    "added",
    "updated",
    "unchanged",
    "destination_only",
    "conflicts",
    "will_change",
    "will_stay_unchanged",
    "destination_after",
)


def normalize_sync_timestamp(value):
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(pytz.utc).replace(tzinfo=None)


def prepare_synced_document(source_doc):
    sync_doc = deepcopy(source_doc)
    sync_time = get_current_time_with_tz()
    if not isinstance(sync_doc.get("updated_at"), datetime):
        sync_doc["updated_at"] = sync_time
    if not isinstance(sync_doc.get("created_at"), datetime):
        sync_doc["created_at"] = sync_doc["updated_at"]
    return sync_doc


def classify_sync_action(source_doc, target_doc):
    """Return the one timestamp-aware action shared by preview and apply."""
    if target_doc is None:
        return "added"

    source_updated_at = normalize_sync_timestamp(source_doc.get("updated_at"))
    target_updated_at = normalize_sync_timestamp(target_doc.get("updated_at"))
    if not source_updated_at or not target_updated_at:
        return "conflicts"
    if source_updated_at > target_updated_at:
        return "updated"
    return "unchanged"


def forecast_sync_collection(source_col, target_col, *, batch_size=None):
    """Count the exact non-destructive actions for one collection."""
    result = {
        "source_documents": 0,
        "destination_documents": 0,
        "added": 0,
        "updated": 0,
        "unchanged": 0,
        "destination_only": 0,
        "conflicts": 0,
    }
    source_ids = set()
    source_documents = source_col.find(
        {"archived": {"$ne": True}},
        {"_id": 1, "updated_at": 1},
    )
    if batch_size and hasattr(source_documents, "batch_size"):
        source_documents = source_documents.batch_size(batch_size)
    for source_doc in source_documents:
        source_id = source_doc["_id"]
        source_ids.add(source_id)
        result["source_documents"] += 1
        target_doc = target_col.find_one(
            {"_id": source_id},
            {"_id": 1, "updated_at": 1},
        )
        result[classify_sync_action(source_doc, target_doc)] += 1

    destination_documents = target_col.find({}, {"_id": 1})
    if batch_size and hasattr(destination_documents, "batch_size"):
        destination_documents = destination_documents.batch_size(batch_size)
    for destination_doc in destination_documents:
        result["destination_documents"] += 1
        if destination_doc["_id"] not in source_ids:
            result["destination_only"] += 1

    result["will_change"] = result["added"] + result["updated"]
    result["will_stay_unchanged"] = (
        result["unchanged"]
        + result["destination_only"]
        + result["conflicts"]
    )
    result["destination_after"] = (
        result["destination_documents"] + result["added"]
    )
    return result


def forecast_collections(runtime, source_client, destination_client):
    """Build per-collection and aggregate timestamp-aware action counts."""
    source_db = source_client[runtime.source_database_name]
    destination_db = destination_client[runtime.destination_database_name]
    collections = {
        name: forecast_sync_collection(
            source_db[name],
            destination_db[name],
            batch_size=runtime.batch_size,
        )
        for name in runtime.requested_collections
    }
    aggregate = {
        field: sum(item[field] for item in collections.values())
        for field in FORECAST_FIELDS
    }
    return {"collections": collections, "aggregate": aggregate}


def sync_collection(source_col, target_col, *, batch_size=None):
    result = {
        "added": 0,
        "updated": 0,
        "skipped": 0,
        "conflicts": 0,
        "conflict_ids": [],
    }
    source_documents = source_col.find({"archived": {"$ne": True}})
    if batch_size and hasattr(source_documents, "batch_size"):
        source_documents = source_documents.batch_size(batch_size)
    for source_doc in source_documents:
        target_doc = target_col.find_one({"_id": source_doc["_id"]})
        action = classify_sync_action(source_doc, target_doc)
        if action == "added":
            target_col.insert_one(prepare_synced_document(source_doc))
            result["added"] += 1
            continue
        if action == "conflicts":
            result["conflicts"] += 1
            result["conflict_ids"].append(str(source_doc["_id"]))
            continue
        if action == "updated":
            target_col.replace_one(
                {"_id": source_doc["_id"]},
                prepare_synced_document(source_doc),
            )
            result["updated"] += 1
        else:
            result["skipped"] += 1
    return result
