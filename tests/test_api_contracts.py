"""Coverage for page, settings, label, and identifier API contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from bson.objectid import ObjectId


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
