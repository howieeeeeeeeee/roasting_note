"""Timestamp-aware synchronization shared by route and operational adapters."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime

import pytz

from roastlogger.time_utils import get_current_time_with_tz


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
        if not target_doc:
            target_col.insert_one(prepare_synced_document(source_doc))
            result["added"] += 1
            continue

        source_updated_at = normalize_sync_timestamp(source_doc.get("updated_at"))
        target_updated_at = normalize_sync_timestamp(target_doc.get("updated_at"))
        if not source_updated_at or not target_updated_at:
            result["conflicts"] += 1
            result["conflict_ids"].append(str(source_doc["_id"]))
            continue

        if source_updated_at > target_updated_at:
            target_col.replace_one(
                {"_id": source_doc["_id"]},
                prepare_synced_document(source_doc),
            )
            result["updated"] += 1
        else:
            result["skipped"] += 1
    return result
