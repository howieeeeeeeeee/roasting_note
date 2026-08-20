"""Coverage for page, settings, label, and identifier API contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from bson.objectid import ObjectId

import roastlogger.blueprints.beans as bean_blueprint


def test_label_image_and_recent_preferences_contract(client, beans_collection):
    marker = f"api-contract-{uuid4().hex[:10]}"
    bean_id = beans_collection.insert_one(
        {
            "name": marker,
            "archived": False,
            "test_data": True,
            "updated_at": datetime(2099, 1, 1, tzinfo=timezone.utc),
            "label": {
                "templateId": "classic",
                "fontPreset": "serif",
                "aspectRatio": "4:3",
            },
        }
    ).inserted_id
    try:
        images = client.get("/api/label/images")
        assert images.status_code == 200
        assert images.json["images"] == ["favicon.svg", "nova.png"]

        preferences = client.get("/api/label/preferences")
        assert preferences.status_code == 200
        assert preferences.json == {
            "templateId": "classic",
            "fontPreset": "serif",
            "aspectRatio": "4:3",
        }
    finally:
        beans_collection.delete_one({"_id": bean_id})


def test_database_settings_validate_modes_and_round_trip(client):
    current = client.get("/api/settings/db")
    assert current.status_code == 200
    assert current.json["mode"] == "local"
    assert current.json["e2e_mode"] is False

    invalid = client.post("/api/settings/db", json={"mode": "replica"})
    assert invalid.status_code == 400
    assert invalid.json["success"] is False

    online = client.post("/api/settings/db", json={"mode": "online"})
    assert online.status_code == 200
    assert online.json["mode"] == "online"
    local = client.post("/api/settings/db", json={"mode": "local"})
    assert local.status_code == 200
    assert local.json["mode"] == "local"


def test_page_routes_render_for_existing_records(
    client,
    created_test_bean,
    created_test_roast,
    roasts_collection,
):
    bean_id = created_test_bean
    roast_id = created_test_roast["roast_id"]
    routes = (
        "/",
        "/beans",
        "/beans/add",
        f"/beans/detail/{bean_id}",
        f"/beans/edit/{bean_id}",
        f"/roast/live/{roast_id}",
        f"/roast/detail/{roast_id}",
        f"/roast/edit/{roast_id}",
    )
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, route

    created = client.get("/roast/new")
    assert created.status_code == 302
    generated_id = ObjectId(created.location.rsplit("/", 1)[-1])
    roasts_collection.delete_one({"_id": generated_id})


def test_bean_detail_stock_zero_action_and_history_contract(
    client,
    beans_collection,
    created_test_bean,
):
    bean_id = ObjectId(created_test_bean)
    positive = client.get(f"/beans/detail/{bean_id}").get_data(as_text=True)
    assert 'id="beanMoreActions"' in positive
    assert "Set stock to zero" in positive
    assert 'id="stockHistoryTableContainer" hidden' in positive
    assert 'id="stockHistoryEmpty">No stock changes recorded.' in positive

    beans_collection.update_one(
        {"_id": bean_id},
        {"$set": {"stock_grams": 0}},
    )
    zero = client.get(f"/beans/detail/{bean_id}").get_data(as_text=True)
    assert 'id="beanMoreActions"' not in zero
    assert "Set stock to zero" not in zero

    beans_collection.update_one(
        {"_id": bean_id},
        {
            "$set": {
                "stock_grams": -35,
                "stock_change_log": [
                    {
                        "event_type": "set_to_zero",
                        "previous_stock_grams": 120,
                        "change_grams": -120,
                        "resulting_stock_grams": 0,
                        "recorded_at": datetime(2026, 8, 20, 10, 0),
                    },
                    {
                        "event_type": "set_to_zero",
                        "previous_stock_grams": -35,
                        "change_grams": 35,
                        "resulting_stock_grams": 0,
                        "recorded_at": datetime(2026, 8, 20, 11, 0),
                    },
                ],
            }
        },
    )
    negative = client.get(f"/beans/detail/{bean_id}").get_data(as_text=True)
    assert 'id="beanMoreActions"' in negative
    history = negative.split('id="stockHistoryBody"', 1)[1]
    assert history.index("-35g") < history.index("120g")
    assert "+35g" in history


def test_bean_list_out_of_stock_filter_labels_match_visibility(
    client,
    beans_collection,
    created_test_bean,
):
    bean_id = ObjectId(created_test_bean)
    beans_collection.update_one(
        {"_id": bean_id},
        {"$set": {"stock_grams": 0}},
    )

    default_view = client.get("/beans").get_data(as_text=True)
    assert "Show Out of Stock" in default_view
    assert f"/beans/detail/{bean_id}" not in default_view

    revealed_view = client.get(
        "/beans?filter_out_of_stock=false"
    ).get_data(as_text=True)
    assert "Hide Out of Stock" in revealed_view
    assert f"/beans/detail/{bean_id}" in revealed_view


def test_invalid_and_missing_identifiers_return_stable_errors(
    client,
    created_test_bean,
):
    page = client.get("/beans/detail/not-an-object-id")
    assert page.status_code == 400
    assert page.get_data(as_text=True) == "Invalid identifier"

    api = client.post("/api/beans/delete/not-an-object-id")
    assert api.status_code == 400
    assert api.json == {
        "success": False,
        "error": "Invalid identifier",
    }

    stock_api = client.post(
        "/api/beans/not-an-object-id/set-stock-zero"
    )
    assert stock_api.status_code == 400
    assert stock_api.json == {
        "success": False,
        "error": "Invalid identifier",
    }

    missing = client.post(
        f"/api/beans/{ObjectId()}/label",
        json={"name": "Missing"},
    )
    assert missing.status_code == 404
    assert missing.json["error"] == "Bean not found"

    malformed = client.post(
        f"/api/beans/{created_test_bean}/label",
        data="{",
        content_type="application/json",
    )
    assert malformed.status_code == 400


def test_stock_zero_conflict_returns_stable_error(client, monkeypatch):
    monkeypatch.setattr(
        bean_blueprint,
        "set_bean_stock_to_zero",
        lambda *_args: {"status": "conflict"},
    )

    response = client.post(
        f"/api/beans/{ObjectId()}/set-stock-zero"
    )

    assert response.status_code == 409
    assert response.json == {
        "success": False,
        "error": "Bean stock changed; refresh and try again",
    }
