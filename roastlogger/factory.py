"""Flask application factory."""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from roastlogger.blueprints import beans, pages, roasts, settings, temperature
from roastlogger.config import default_config
from roastlogger.database import (
    get_beans_collection,
    get_roasts_collection,
    init_database,
)
from roastlogger.time_utils import (
    format_date_in_timezone,
    format_seconds,
    get_local_timezone,
)


ROOT = Path(__file__).resolve().parents[1]


class TLSHandshakeFilter(logging.Filter):
    def filter(self, record):
        message = str(record.getMessage())
        if "code 400" in message and "Bad request version" in message:
            if "\\x" in message or len(message) > 150:
                return False
        return True


def _configure_logging():
    logger = logging.getLogger("werkzeug")
    if not any(isinstance(item, TLSHandshakeFilter) for item in logger.filters):
        logger.addFilter(TLSHandshakeFilter())


def _register_template_helpers(app):
    @app.context_processor
    def inject_nav_counts():
        try:
            roast_count = get_roasts_collection().count_documents({})
            bean_count = get_beans_collection().count_documents(
                {"archived": {"$ne": True}}
            )
        except Exception:
            roast_count = 0
            bean_count = 0
        return {
            "nav_roast_count": roast_count,
            "nav_bean_count": bean_count,
        }

    @app.template_filter("format_date")
    def format_date(value):
        return format_date_in_timezone(value, get_local_timezone())

    app.add_template_filter(format_seconds, "format_seconds")


def create_app(config_overrides=None):
    load_dotenv()
    app = Flask(
        __name__,
        static_folder=str(ROOT / "static"),
        template_folder=str(ROOT / "templates"),
    )
    app.config.update(default_config())
    app.config["REPOSITORY_ROOT"] = str(ROOT)
    if config_overrides:
        app.config.update(config_overrides)

    _configure_logging()
    init_database(app)
    _register_template_helpers(app)
    for feature_blueprint in (
        pages.blueprint,
        beans.blueprint,
        roasts.blueprint,
        temperature.blueprint,
        settings.blueprint,
    ):
        app.register_blueprint(feature_blueprint)
    return app
