"""In-memory MongoDB surface for guarded-sync tests."""

from __future__ import annotations

from copy import deepcopy


class FakeCursor(list):
    def __init__(self, values):
        super().__init__(deepcopy(values))
        self.requested_batch_size = None

    def batch_size(self, value):
        self.requested_batch_size = value
        return self


class FakeCollection:
    def __init__(self, documents=None, *, fail_find=False):
        self.documents = {
            document["_id"]: deepcopy(document)
            for document in documents or []
        }
        self.fail_find = fail_find
        self.write_count = 0

    def find(self, query):
        if self.fail_find:
            raise RuntimeError("simulated collection failure")
        if query == {}:
            values = self.documents.values()
        elif query == {"archived": {"$ne": True}}:
            values = (
                document
                for document in self.documents.values()
                if document.get("archived") is not True
            )
        else:
            raise AssertionError(f"unexpected query: {query}")
        return FakeCursor(list(values))

    def find_one(self, query):
        value = self.documents.get(query["_id"])
        return deepcopy(value) if value else None

    def insert_one(self, document):
        self.documents[document["_id"]] = deepcopy(document)
        self.write_count += 1

    def replace_one(self, query, document):
        self.documents[query["_id"]] = deepcopy(document)
        self.write_count += 1

    def count_documents(self, query):
        if query == {}:
            return len(self.documents)
        if query == {"archived": {"$ne": True}}:
            return sum(
                document.get("archived") is not True
                for document in self.documents.values()
            )
        raise AssertionError(f"unexpected count query: {query}")


class FakeDatabase:
    def __init__(self, collections=None):
        self.collections = dict(collections or {})

    def __getitem__(self, name):
        return self.collections.setdefault(name, FakeCollection())

    def __getattr__(self, name):
        return self[name]

    def list_collection_names(self):
        return list(self.collections)


class FakeAdmin:
    def __init__(self, *, available=True):
        self.available = available

    def command(self, name):
        if name != "ping":
            raise AssertionError(f"unexpected admin command: {name}")
        if not self.available:
            raise RuntimeError("credential-bearing database failure")
        return {"ok": 1}


class FakeClient:
    def __init__(self, databases=None, *, available=True):
        self.databases = dict(databases or {})
        self.admin = FakeAdmin(available=available)
        self.closed = False

    def __getitem__(self, name):
        return self.databases.setdefault(name, FakeDatabase())

    def close(self):
        self.closed = True


class FakeConnections:
    def __init__(self, online_client, local_client):
        self.online_client = online_client
        self.local_client = local_client
        self.online_db = online_client["roastlogger"]
        self.local_db = local_client["roastlogger"]
