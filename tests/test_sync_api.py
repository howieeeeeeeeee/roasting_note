"""
Tests for timestamp-aware local/online database sync.
"""
from copy import deepcopy
from datetime import datetime

import pytest
from bson.objectid import ObjectId

import app as app_module


class FakeCollection:
    """Small in-memory collection covering the sync_collection API surface."""

    def __init__(self, docs=None):
        self.docs = {}
        for doc in docs or []:
            self.docs[doc["_id"]] = deepcopy(doc)

    def find(self, query):
        if query == {"archived": {"$ne": True}}:
            return [
                deepcopy(doc)
                for doc in self.docs.values()
                if doc.get("archived") is not True
            ]
        raise AssertionError(f"Unexpected find query: {query}")

    def find_one(self, query):
        if "_id" not in query:
            raise AssertionError(f"Unexpected find_one query: {query}")
        doc = self.docs.get(query["_id"])
        return deepcopy(doc) if doc else None

    def insert_one(self, doc):
        self.docs[doc["_id"]] = deepcopy(doc)

    def replace_one(self, query, doc):
        if "_id" not in query:
            raise AssertionError(f"Unexpected replace_one query: {query}")
        self.docs[query["_id"]] = deepcopy(doc)


def make_sync_doc(collection_type, updated_at=None, value="source", doc_id=None):
    doc = {
        "_id": doc_id or ObjectId(),
        "archived": False,
        "created_at": datetime(2026, 5, 1, 8, 0, 0),
        "value": value,
    }
    if updated_at is not None:
        doc["updated_at"] = updated_at

    if collection_type == "beans":
        doc["name"] = f"{value} bean"
    else:
        doc["title"] = f"{value} roast"
        doc["key_timings"] = []
        doc["temp_curve"] = []
        doc["reviews"] = []

    return doc


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_inserts_missing_target_document(collection_type):
    doc = make_sync_doc(collection_type, datetime(2026, 5, 1, 9, 0, 0))
    source = FakeCollection([doc])
    target = FakeCollection()

    result = app_module.sync_collection(source, target)

    assert result == {
        "added": 1,
        "updated": 0,
        "skipped": 0,
        "conflicts": 0,
        "conflict_ids": [],
    }
    assert target.docs[doc["_id"]]["value"] == "source"
    assert isinstance(target.docs[doc["_id"]]["created_at"], datetime)
    assert isinstance(target.docs[doc["_id"]]["updated_at"], datetime)


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_fills_timestamps_when_inserting_legacy_document(collection_type):
    doc = make_sync_doc(collection_type, None)
    doc.pop("created_at")
    source = FakeCollection([doc])
    target = FakeCollection()

    result = app_module.sync_collection(source, target)

    synced_doc = target.docs[doc["_id"]]
    assert result["added"] == 1
    assert isinstance(synced_doc["created_at"], datetime)
    assert isinstance(synced_doc["updated_at"], datetime)


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_updates_older_target_document(collection_type):
    doc_id = ObjectId()
    source_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 10, 0, 0),
        "newer",
        doc_id,
    )
    target_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 9, 0, 0),
        "older",
        doc_id,
    )
    source = FakeCollection([source_doc])
    target = FakeCollection([target_doc])

    result = app_module.sync_collection(source, target)

    assert result["updated"] == 1
    assert result["added"] == 0
    assert result["skipped"] == 0
    assert result["conflicts"] == 0
    assert target.docs[doc_id]["value"] == "newer"


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_fills_missing_created_at_when_updating_target(collection_type):
    doc_id = ObjectId()
    source_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 10, 0, 0),
        "newer",
        doc_id,
    )
    source_doc.pop("created_at")
    target_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 9, 0, 0),
        "older",
        doc_id,
    )
    source = FakeCollection([source_doc])
    target = FakeCollection([target_doc])

    result = app_module.sync_collection(source, target)

    assert result["updated"] == 1
    assert target.docs[doc_id]["value"] == "newer"
    assert target.docs[doc_id]["created_at"] == source_doc["updated_at"]


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_skips_newer_target_document(collection_type):
    doc_id = ObjectId()
    source_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 9, 0, 0),
        "older",
        doc_id,
    )
    target_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 10, 0, 0),
        "newer",
        doc_id,
    )
    source = FakeCollection([source_doc])
    target = FakeCollection([target_doc])

    result = app_module.sync_collection(source, target)

    assert result["updated"] == 0
    assert result["skipped"] == 1
    assert result["conflicts"] == 0
    assert target.docs[doc_id]["value"] == "newer"


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_skips_equal_timestamp_target_document(collection_type):
    doc_id = ObjectId()
    timestamp = datetime(2026, 5, 1, 9, 0, 0)
    source_doc = make_sync_doc(collection_type, timestamp, "source", doc_id)
    target_doc = make_sync_doc(collection_type, timestamp, "target", doc_id)
    source = FakeCollection([source_doc])
    target = FakeCollection([target_doc])

    result = app_module.sync_collection(source, target)

    assert result["updated"] == 0
    assert result["skipped"] == 1
    assert result["conflicts"] == 0
    assert target.docs[doc_id]["value"] == "target"


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_reports_missing_source_timestamp_as_conflict(collection_type):
    doc_id = ObjectId()
    source_doc = make_sync_doc(collection_type, None, "source", doc_id)
    target_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 9, 0, 0),
        "target",
        doc_id,
    )
    source = FakeCollection([source_doc])
    target = FakeCollection([target_doc])

    result = app_module.sync_collection(source, target)

    assert result["updated"] == 0
    assert result["skipped"] == 0
    assert result["conflicts"] == 1
    assert result["conflict_ids"] == [str(doc_id)]
    assert target.docs[doc_id]["value"] == "target"


@pytest.mark.parametrize("collection_type", ["beans", "roasts"])
def test_sync_reports_missing_target_timestamp_as_conflict(collection_type):
    doc_id = ObjectId()
    source_doc = make_sync_doc(
        collection_type,
        datetime(2026, 5, 1, 9, 0, 0),
        "source",
        doc_id,
    )
    target_doc = make_sync_doc(collection_type, None, "target", doc_id)
    source = FakeCollection([source_doc])
    target = FakeCollection([target_doc])

    result = app_module.sync_collection(source, target)

    assert result["updated"] == 0
    assert result["skipped"] == 0
    assert result["conflicts"] == 1
    assert result["conflict_ids"] == [str(doc_id)]
    assert target.docs[doc_id]["value"] == "target"
