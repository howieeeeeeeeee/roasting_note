"""Regression coverage for application and live-page module boundaries."""

import json
import re

from bson.objectid import ObjectId
from roastlogger import create_app


EXPECTED_ROUTES = {
    ("/", "GET", "index"),
    ("/favicon.ico", "GET", "favicon"),
    ("/beans", "GET", "beans_list"),
    ("/beans/add", "GET", "beans_add_form"),
    ("/beans/detail/<bean_id>", "GET", "beans_detail"),
    ("/beans/edit/<bean_id>", "GET", "beans_edit_form"),
    ("/roast/new", "GET", "roast_new"),
    ("/roast/live/<roast_id>", "GET", "roast_live"),
    ("/roast/detail/<roast_id>", "GET", "roast_detail"),
    ("/roast/edit/<roast_id>", "GET", "roast_edit_form"),
    ("/api/beans/add", "POST", "api_beans_add"),
    ("/api/beans/edit/<bean_id>", "POST", "api_beans_edit"),
    ("/api/beans/delete/<bean_id>", "POST", "api_beans_delete"),
    (
        "/api/beans/<bean_id>/set-stock-zero",
        "POST",
        "api_beans_set_stock_zero",
    ),
    ("/api/beans/<bean_id>/label", "POST", "api_beans_label"),
    ("/api/label/images", "GET", "api_label_images"),
    ("/api/label/preferences", "GET", "api_label_preferences"),
    ("/api/roast/create", "POST", "api_roast_create"),
    ("/api/roast/start/<roast_id>", "POST", "api_roast_start"),
    ("/api/roast/end/<roast_id>", "POST", "api_roast_end"),
    ("/api/roast/update_title/<roast_id>", "POST", "api_roast_update_title"),
    ("/api/roast/update_setup/<roast_id>", "POST", "api_roast_update_setup"),
    (
        "/api/roast/complete_draft/<roast_id>",
        "POST",
        "api_roast_complete_draft",
    ),
    ("/api/roast/add_timing/<roast_id>", "POST", "api_roast_add_timing"),
    ("/api/roast/add_event/<roast_id>", "POST", "api_roast_add_event"),
    (
        "/api/roast/log_temp_local/<roast_id>",
        "POST",
        "api_roast_log_temp_local",
    ),
    ("/api/roast/update/<roast_id>", "POST", "api_roast_update"),
    ("/api/roast/delete/<roast_id>", "POST", "api_roast_delete"),
    ("/api/roast/add_review/<roast_id>", "POST", "api_roast_add_review"),
    (
        "/api/roast/update_review/<roast_id>/<review_id>",
        "POST",
        "api_roast_update_review",
    ),
    (
        "/api/roast/delete_review/<roast_id>/<review_id>",
        "POST",
        "api_roast_delete_review",
    ),
    ("/api/roast/sync_state/<roast_id>", "POST", "api_roast_sync_state"),
    ("/api/temp/current_fast", "GET", "api_temp_current_fast"),
    ("/api/temp/test_connection", "GET", "api_temp_test_connection"),
    ("/api/temp/current", "GET", "api_temp_current"),
    ("/api/settings/db", "GET", "api_get_db_settings"),
    ("/api/settings/db", "POST", "api_set_db_settings"),
    ("/api/settings/sensor", "GET", "api_get_sensor_settings"),
    ("/api/settings/sensor", "POST", "api_set_sensor_settings"),
    (
        "/api/sync/online-to-local",
        "POST",
        "api_sync_online_to_local",
    ),
    (
        "/api/sync/local-to-online",
        "POST",
        "api_sync_local_to_online",
    ),
    (
        "/api/sync/preflight/<direction>",
        "POST",
        "api_sync_preflight",
    ),
    ("/api/sync/runs/active", "GET", "api_sync_active_run"),
    ("/api/sync/runs/<run_id>/backup", "POST", "api_sync_backup"),
    ("/api/sync/runs/<run_id>/apply", "POST", "api_sync_apply"),
    ("/api/sync/runs/<run_id>/cancel", "POST", "api_sync_cancel"),
    ("/api/db/clean-test-data", "POST", "api_clean_test_data"),
    ("/api/db/clean-local", "POST", "api_clean_local_db"),
}


def test_route_manifest_preserves_public_contract():
    app = create_app({"TESTING": True})
    actual = {
        (rule.rule, method, rule.endpoint)
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    assert actual == EXPECTED_ROUTES


def test_factory_allows_local_database_and_sensor_overrides():
    app = create_app(
        {
            "TESTING": True,
            "LOCAL_DB_NAME": "roastlogger_factory_test",
            "TEMP_SENSOR_URL": "http://127.0.0.1:9911/temp",
        }
    )
    connections = app.extensions["roastlogger_databases"]
    assert connections.local_db.name == "roastlogger_factory_test"
    assert app.config["TEMP_SENSOR_URL"] == "http://127.0.0.1:9911/temp"


def test_live_roast_uses_one_json_bootstrap_and_module_entry():
    app = create_app({"TESTING": True})
    roast_id = ObjectId()
    roast = {
        "_id": roast_id,
        "title": "Module Boundary",
        "lifecycle_state": "draft",
        "roast_start_time": None,
        "key_timings": [],
        "temp_curve": [],
    }
    with app.test_request_context():
        rendered = app.jinja_env.get_template("roast_live.html").render(
            roast=roast,
            beans=[],
        )

    match = re.search(
        r'<script type="application/json" id="live-roast-config">'
        r"(.*?)</script>",
        rendered,
    )
    assert match
    assert rendered.count('id="live-roast-config"') == 1
    assert 'type="module"' in rendered
    assert "js/live-roast/index.js" in rendered
    assert json.loads(match.group(1)) == {
        "roastId": str(roast_id),
        "roastStarted": False,
        "roastEnded": False,
        "roastStartTime": None,
    }
