"""Database connection and selection boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from flask import current_app, session
from pymongo import MongoClient


@dataclass
class DatabaseConnections:
    online_client: MongoClient
    local_client: MongoClient
    online_db: object
    local_db: object

    @classmethod
    def from_config(cls, config) -> "DatabaseConnections":
        online_client = MongoClient(config["MONGO_URI"])
        local_client = MongoClient(config["MONGO_URI_LOCAL"])
        return cls(
            online_client=online_client,
            local_client=local_client,
            online_db=online_client[config["ONLINE_DB_NAME"]],
            local_db=local_client[config["LOCAL_DB_NAME"]],
        )


def init_database(app) -> DatabaseConnections:
    connections = DatabaseConnections.from_config(app.config)
    app.extensions["roastlogger_databases"] = connections
    return connections


def get_connections() -> DatabaseConnections:
    return current_app.extensions["roastlogger_databases"]


def get_current_db_mode() -> str:
    mode = session.get("db_mode", current_app.config["DEFAULT_DB"])
    return mode if mode in {"local", "online"} else "local"


def get_beans_collection():
    connections = get_connections()
    if get_current_db_mode() == "online":
        return connections.online_db.beans
    return connections.local_db.beans


def get_roasts_collection():
    connections = get_connections()
    if get_current_db_mode() == "online":
        return connections.online_db.roasts
    return connections.local_db.roasts
