from datetime import datetime, timezone

import pytz

import app as app_module


def test_format_date_treats_naive_mongo_datetime_as_utc(monkeypatch):
    monkeypatch.setattr(app_module, "local_tz", pytz.timezone("America/New_York"))

    stored_utc = datetime(2026, 5, 3, 0, 40)

    assert app_module.format_date(stored_utc) == "2026-05-02 20:40"


def test_format_date_converts_aware_datetime_to_operator_timezone(monkeypatch):
    monkeypatch.setattr(app_module, "local_tz", pytz.timezone("America/New_York"))

    stored_utc = datetime(2026, 5, 3, 0, 40, tzinfo=timezone.utc)

    assert app_module.format_date(stored_utc) == "2026-05-02 20:40"
