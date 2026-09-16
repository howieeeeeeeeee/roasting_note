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


def test_guarded_settings_sync_markup_uses_click_only_safe_phase_controls():
    template = Path("templates/base.html").read_text(encoding="utf-8")
    script = Path("static/js/settings-sheet.js").read_text(encoding="utf-8")

    assert "Guarded Database Sync" in template
    assert "data.backup_confirmation" not in script
    assert "data.apply_confirmation" not in script
    assert "appendSyncForecast(result, plan.forecast)" in script
    assert '"1. Create and verify backup"' in script
    assert "`2. Apply ${changeCount} change" in script
    assert 'fetch("/api/sync/runs/active")' in script
    assert "`/api/sync/runs/${runId}/backup`" in script
    assert "`/api/sync/runs/${runId}/apply`" in script
    assert "`/api/sync/runs/${runId}/cancel`" in script
    assert "Type the exact confirmation" not in script
    assert "sync-confirmation-token" not in script
    assert "line.appendChild(document.createTextNode(value))" in script
    assert "Object.entries(data.sync.collections)" in script
    assert '"Verified manifest SHA-256"' in script
    assert 'data.status === "cancelled_after_backup"' in script
    assert '"Cancellation audit needs recovery attention"' in script
    assert "body: JSON.stringify(body)" in script
    assert "const expectedExistingRun = syncRunActive" in script
    assert "expectedExistingRun" in script
    assert "renderAwaitingApply(data.active, phaseError)" in script
    assert "focusVisibleSyncControl(focusTarget)" in script


def test_label_image_and_recent_preferences_contract(client, app, beans_collection, tmp_path, monkeypatch):
    image_directory = tmp_path / "img"
    image_directory.mkdir()
    for filename in ("nova.png", "favicon.svg", "ignored.txt"):
        (image_directory / filename).touch()
    monkeypatch.setattr(app, "static_folder", str(tmp_path))
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


def test_quiet_compact_fonts_and_navigation_render_by_route(
    client,
    created_test_bean,
    created_test_roast,
):
    roasts = client.get("/").get_data(as_text=True)
    beans = client.get("/beans").get_data(as_text=True)
    bean_detail = client.get(
        f"/beans/detail/{created_test_bean}"
    ).get_data(as_text=True)
    live = client.get(
        f"/roast/live/{created_test_roast['roast_id']}"
    ).get_data(as_text=True)

    for ordinary_page in (roasts, beans, live):
        assert ordinary_page.count("fonts.googleapis.com/css2") == 1
        assert "Barlow+Condensed" not in ordinary_page
        assert "Playfair+Display" not in ordinary_page
        assert "Roboto+Slab" not in ordinary_page

    assert bean_detail.count("fonts.googleapis.com/css2") == 2
    assert "Barlow+Condensed" in bean_detail
    assert "Playfair+Display" in bean_detail
    assert "Roboto+Slab" in bean_detail

    assert re.search(
        r'data-nav-tab="roasts"[^>]*aria-current="page"',
        roasts,
    )
    assert re.search(
        r'data-nav-tab="beans"[^>]*aria-current="page"',
        beans,
    )
    assert roasts.count('class="nav-tab-count"') == 2
    assert beans.count('class="nav-tab-count"') == 2
    assert roasts.count('class="nav-active-indicator"') == 1
    assert beans.count('class="nav-active-indicator"') == 1
    assert 'href="/" data-nav-tab="roasts"' in beans
    assert 'href="/beans" data-nav-tab="beans"' in roasts
    assert 'class="container no-route-transition"' in live


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
            'aria-valuetext="300g remaining of 2000g purchased (15.0%)"'
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


def test_live_roast_raw_names_and_recorded_fc_bootstrap(client, created_test_roast, roasts_collection):
    import json
    import re
    from bson import ObjectId
    roast_id = created_test_roast["roast_id"]
    roasts_collection.update_one({"_id": ObjectId(roast_id)}, {"$set": {
        "key_timings": [{"event_name": "First Crack Start", "time_seconds": 60}]
    }})
    html = client.get(f"/roast/live/{roast_id}").get_data(as_text=True)
    config = json.loads(re.search(r'id="live-roast-config">(.*?)</script>', html, re.S).group(1))
    assert config["keyTimings"][0]["time_seconds"] == 60
    assert 'data-bean-name="Test Ethiopian Yirgacheffe"' in html
    assert 'id="fcElapsedValue"' in html
    assert 'id="fsFcTimeDisplay"' in html
    assert html.count('class="temperature-reading"') == 2


def test_roast_detail_uses_linked_bean_origin_and_processing(client, created_test_roast, beans_collection):
    from bson import ObjectId
    bean_id = created_test_roast["bean_id"]
    beans_collection.update_one({"_id": ObjectId(bean_id)}, {"$set": {"origin": "Origin example", "process": "Honey example"}})
    route = f'/roast/detail/{created_test_roast["roast_id"]}'
    html = client.get(route).get_data(as_text=True)
    assert '<strong>Origin:</strong> Origin example' in html
    assert '<strong>Processing:</strong> Honey example' in html
    beans_collection.update_one({"_id": ObjectId(bean_id)}, {"$unset": {"origin": "", "process": ""}})
    html = client.get(route).get_data(as_text=True)
    assert '<strong>Origin:</strong> Not specified' in html
    assert '<strong>Processing:</strong> Not specified' in html


def test_completed_roast_links_to_available_bean(client, created_test_roast, roasts_collection, beans_collection):
    from datetime import datetime
    from bson import ObjectId

    roast_id = ObjectId(created_test_roast["roast_id"])
    bean_id = ObjectId(created_test_roast["bean_id"])
    route = f"/roast/detail/{roast_id}"
    for status in ("draft", "started", "completed"):
        roasts_collection.update_one({"_id": roast_id}, {"$set": {"lifecycle_status": status}})
        html = client.get(route).get_data(as_text=True)
        assert ('id="viewBeanButton"' in html) == (status == "completed")
    assert f'href="/beans/detail/{bean_id}" class="btn btn-secondary" id="viewBeanButton"' in html
    assert client.get(f"/beans/detail/{bean_id}").status_code == 200

    # Legacy completion timestamps also expose the navigation action.
    roasts_collection.update_one({"_id": roast_id}, {
        "$unset": {"lifecycle_status": ""}, "$set": {"roast_end_time": datetime(2026, 9, 15)}})
    assert 'id="viewBeanButton"' in client.get(route).get_data(as_text=True)
    beans_collection.update_one({"_id": bean_id}, {"$set": {"archived": True}})
    assert 'id="viewBeanButton"' not in client.get(route).get_data(as_text=True)
    roasts_collection.update_one({"_id": roast_id}, {"$set": {"bean_id": ObjectId()}})
    assert 'id="viewBeanButton"' not in client.get(route).get_data(as_text=True)
    roasts_collection.update_one({"_id": roast_id}, {"$unset": {"bean_id": ""}})
    assert 'id="viewBeanButton"' not in client.get(route).get_data(as_text=True)


def test_last_roast_dates_match_in_list_and_detail(client, app, created_test_bean, roasts_collection, monkeypatch):
    from datetime import datetime
    from bson import ObjectId
    import re

    monkeypatch.setitem(app.config, "TIMEZONE", "America/New_York")
    bean_id = ObjectId(created_test_bean)
    inserted = []

    def add(**values):
        inserted.append(roasts_collection.insert_one({
            "bean_id": bean_id, "title": "Last roast regression", "test_data": True,
            "roast_date": datetime(2026, 9, 15), "key_timings": [], "temp_curve": [],
            **values,
        }).inserted_id)

    def assert_date(expected):
        detail = client.get(f"/beans/detail/{bean_id}").get_data(as_text=True)
        assert f'id="lastRoastDate">{expected}</span>' in detail
        listing = client.get("/beans").get_data(as_text=True)
        row = next(row for row in re.findall(r'<tr class="bean-row.*?</tr>', listing, re.S)
                   if f'/beans/detail/{bean_id}' in row)
        assert re.search(r'class="date-cell bean-last-roast">\s*' + re.escape(expected), row)

    try:
        assert_date("Not roasted yet")
        add(lifecycle_status="draft")
        add(lifecycle_status="started", roast_start_time=datetime(2026, 9, 15, 2))
        add(lifecycle_status="completed", archived=True, roast_start_time=datetime(2026, 9, 16))
        assert_date("Not roasted yet")
        # Start time wins over a later setup date; UTC crossing midnight renders locally.
        add(lifecycle_status="completed", roast_start_time=datetime(2026, 9, 12, 1, 30))
        assert_date("2026-09-11 21:30")
        # Manually completed records have no start time, and use roast_date.
        add(lifecycle_status="completed", roast_date=datetime(2026, 9, 13, 2))
        assert_date("2026-09-12 22:00")
        # Legacy completed roasts are eligible; unrelated beans and missing dates are not.
        add(roast_start_time=datetime(2026, 9, 14, 3), roast_end_time=datetime(2026, 9, 14, 3, 10))
        add(lifecycle_status="completed", bean_id=ObjectId(), roast_date=datetime(2026, 9, 20))
        add(lifecycle_status="completed", roast_date=None)
        assert_date("2026-09-13 23:00")
    finally:
        roasts_collection.delete_many({"_id": {"$in": inserted}, "test_data": True})
