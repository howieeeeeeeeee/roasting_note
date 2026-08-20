"""Contracts for compact Bean and Roast management screens."""

from __future__ import annotations

from pathlib import Path


MANAGEMENT_CSS = Path("static/css/screens/management.css")


def _template(name: str) -> str:
    return Path("templates", name).read_text(encoding="utf-8")


def _assert_in_source_order(source: str, fragments: tuple[str, ...]) -> None:
    positions = [source.index(fragment) for fragment in fragments]
    assert positions == sorted(positions)


def test_management_stylesheet_is_loaded_and_scoped() -> None:
    entrypoint = Path("static/css/style.css").read_text(encoding="utf-8")
    css = MANAGEMENT_CSS.read_text(encoding="utf-8")

    assert "@import url('screens/management.css');" in entrypoint
    assert ".management-page" in css
    assert ".management-form" in css
    assert ".management-detail" in css
    assert ".management-table-container" in css
    assert ".live-" not in css
    assert "h-screen" not in css


def test_management_css_preserves_targets_and_responsive_contracts() -> None:
    css = MANAGEMENT_CSS.read_text(encoding="utf-8")

    assert "min-height: var(--control-min, 44px);" in css
    assert "@media (min-width: 1024px)" in css
    assert "@media (max-width: 767px)" in css
    assert "grid-template-columns: minmax(0, 1fr);" in css
    assert "repeat(4, minmax(0, 1fr))" in css
    assert "overflow-x: auto;" in css
    assert "scrollbar-gutter: stable;" in css


def test_management_action_row_is_safe_and_print_neutral() -> None:
    css = MANAGEMENT_CSS.read_text(encoding="utf-8")

    action_rule = css.split(".management-form-actions {", 1)[1].split("}", 1)[0]
    assert "position: sticky;" in action_rule
    assert "bottom: 0;" in action_rule
    assert "env(safe-area-inset-bottom)" in action_rule
    assert "background: var(--bg);" in action_rule
    assert "scroll-margin-block-end" in css

    print_rule = css.split("@media print", 1)[1]
    assert ".management-form-actions" in print_rule
    assert "position: static;" in print_rule


def test_management_templates_keep_field_and_action_order() -> None:
    bean_form = _template("beans_form.html")
    roast_form = _template("roast_edit.html")

    _assert_in_source_order(
        bean_form,
        (
            'name="name"',
            'name="origin"',
            'name="process"',
            'name="supplier"',
            'name="color"',
            'name="short_flavor_notes"',
            'name="notes"',
            'name="purchase_date"',
            'name="purchase_weight_grams"',
            'name="purchase_price_total"',
            'name="stock_grams"',
            "management-form-actions",
        ),
    )
    _assert_in_source_order(
        roast_form,
        (
            'name="title"',
            'name="bean_id"',
            'name="roast_date"',
            'name="roaster"',
            'name="temp_measurement_method"',
            'name="ambient_temp_celsius"',
            'name="ambient_humidity"',
            'name="original_weight_grams"',
            'name="roasted_weight_grams"',
            'name="general_notes"',
            "management-form-actions",
        ),
    )
    assert "Save Changes" in roast_form
    assert roast_form.index("Save Changes") < roast_form.index(">Cancel<")
    assert bean_form.index("Bean</button>") < bean_form.index(">Cancel<")


def test_management_templates_preserve_tables_and_stock_meter() -> None:
    roast_list = _template("index.html")
    bean_list = _template("beans_list.html")
    bean_detail = _template("beans_detail.html")

    assert '<table class="roasts-table">' in roast_list
    assert '<table class="beans-table">' in bean_list
    assert "management-table-container" in roast_list
    assert "management-table-container" in bean_list
    assert "management-table-container" in bean_detail

    assert '<col class="beans-col-stock">' in bean_list
    assert 'class="bean-stock-cell"' in bean_list
    assert 'class="stock-indicator ' in bean_list
    assert 'role="progressbar"' in bean_list
    assert 'aria-valuetext="{{ stock_grams }}g remaining' in bean_list
    assert "--stock-remaining-percent" in bean_list


def test_management_routes_render_compact_roots(
    client,
    created_test_bean,
    created_test_roast,
) -> None:
    roast_id = created_test_roast["roast_id"]
    routes_and_hooks = (
        ("/", "management-page--list"),
        ("/beans", "management-page--list"),
        ("/beans/add", "management-form--bean"),
        (f"/beans/edit/{created_test_bean}", "management-form--bean"),
        (f"/beans/detail/{created_test_bean}", "management-detail--bean"),
        (f"/roast/edit/{roast_id}", "management-form--roast"),
        (f"/roast/detail/{roast_id}", "management-detail--roast"),
    )

    for route, hook in routes_and_hooks:
        response = client.get(route)
        assert response.status_code == 200, route
        html = response.get_data(as_text=True)
        assert 'class="management-page ' in html, route
        assert hook in html, route


def test_live_roast_template_has_no_management_layout_hook() -> None:
    live_template = _template("roast_live.html")

    assert "management-page" not in live_template
    assert "management-form" not in live_template
    assert "management-detail" not in live_template
