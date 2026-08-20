"""Coverage for page, settings, label, and identifier API contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import uuid4

from bson.objectid import ObjectId

import roastlogger.blueprints.beans as bean_blueprint


def _bean_list_row(html: str, bean_name: str) -> str:
    rows = re.findall(
        r'<tr class="bean-row clickable-row".*?</tr>',
        html,
        flags=re.DOTALL,
    )
    return next(row for row in rows if bean_name in row)


def test_guarded_settings_sync_markup_uses_typed_safe_phase_controls():
    template = Path("templates/base.html").read_text(encoding="utf-8")

    assert "Guarded Database Sync" in template
    assert "data.backup_confirmation" in template
    assert "data.apply_confirmation" in template
    assert "'/api/sync/runs/active'" in template
    assert "`/api/sync/runs/${runId}/backup`" in template
    assert "`/api/sync/runs/${runId}/apply`" in template
    assert "`/api/sync/runs/${runId}/cancel`" in template
    assert "required.textContent = token" in template
    assert "line.appendChild(document.createTextNode(value))" in template
    assert "Object.entries(data.sync.collections)" in template
    assert "'Verified manifest SHA-256'" in template
    assert "data.status === 'cancelled_after_backup'" in template
    assert "'Cancellation audit needs recovery attention'" in template
    assert "body: JSON.stringify(body)" in template
    assert "const expectedExistingRun = syncRunActive" in template
    assert "expectedExistingRun" in template
    assert "renderAwaitingApply(data.active, phaseError)" in template
    assert "queueMicrotask(() => input.focus())" in template


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


def test_bean_list_stock_remaining_meter_contract(client, beans_collection):
    marker = f"stock-meter-{uuid4().hex[:10]}"
    cases = [
        (f"{marker}-ratio", 300, 2000),
        (f"{marker}-zero", 0, 2000),
        (f"{marker}-negative", -35, 2000),
        (f"{marker}-above", 2500, 2000),
        (f"{marker}-missing", 450, None),
        (f"{marker}-zero-baseline", 450, 0),
        (f"{marker}-negative-baseline", 450, -100),
        (f"{marker}-non-integer-baseline", 450, 2000.0),
    ]
    documents = []
    for name, stock_grams, purchase_weight_grams in cases:
        document = {
            "name": name,
            "stock_grams": stock_grams,
            "archived": False,
            "test_data": True,
        }
        if purchase_weight_grams is not None:
            document["purchase_weight_grams"] = purchase_weight_grams
        documents.append(document)

    result = beans_collection.insert_many(documents)
    try:
        html = client.get(
            "/beans?filter_out_of_stock=false"
        ).get_data(as_text=True)

        ratio_row = _bean_list_row(html, f"{marker}-ratio")
        assert "300g left" in ratio_row
        assert 'role="progressbar"' in ratio_row
        assert 'aria-valuemin="0"' in ratio_row
        assert 'aria-valuemax="100"' in ratio_row
        assert 'aria-valuenow="15.0"' in ratio_row
        assert (
            'aria-valuetext="300g remaining of 2000g original (15.0%)"'
            in ratio_row
        )
        assert '--stock-remaining-percent: 15.0%;' in ratio_row
        visible_ratio_copy = re.sub(r"<[^>]+>", " ", ratio_row)
        assert "%" not in visible_ratio_copy
        assert "consumed" not in visible_ratio_copy.lower()

        zero_row = _bean_list_row(html, f"{marker}-zero")
        assert "0g left" in zero_row
        assert 'aria-valuenow="0"' in zero_row
        assert '--stock-remaining-percent: 0%;' in zero_row

        negative_row = _bean_list_row(html, f"{marker}-negative")
        assert "-35g left" in negative_row
        assert 'class="stock-badge stock-low"' in negative_row
        assert 'aria-valuenow="0"' in negative_row
        assert '--stock-remaining-percent: 0%;' in negative_row

        above_row = _bean_list_row(html, f"{marker}-above")
        assert "2500g left" in above_row
        assert 'aria-valuenow="100"' in above_row
        assert '--stock-remaining-percent: 100%;' in above_row

        for suffix in (
            "missing",
            "zero-baseline",
            "negative-baseline",
            "non-integer-baseline",
        ):
            fallback_row = _bean_list_row(html, f"{marker}-{suffix}")
            assert "450g left" in fallback_row
            assert 'role="progressbar"' not in fallback_row

        sorted_html = client.get(
            "/beans?filter_out_of_stock=false&sort_by=stock&sort_order=asc"
        ).get_data(as_text=True)
        assert sorted_html.index(f"{marker}-negative") < sorted_html.index(
            f"{marker}-zero"
        )
        assert sorted_html.index(f"{marker}-zero") < sorted_html.index(
            f"{marker}-ratio"
        )
        assert sorted_html.index(f"{marker}-ratio") < sorted_html.index(
            f"{marker}-above"
        )
        assert f"/beans/detail/{result.inserted_ids[0]}" in ratio_row
    finally:
        beans_collection.delete_many({"_id": {"$in": result.inserted_ids}})


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
