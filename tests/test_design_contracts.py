"""Static contracts for the Quiet Compact design foundations and navigation."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _relative_luminance(hex_color: str) -> float:
    values = [
        int(hex_color[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    ]
    linear = [
        value / 12.92
        if value <= 0.04045
        else ((value + 0.055) / 1.055) ** 2.4
        for value in values
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def _composite(foreground: str, background: str, alpha: float) -> str:
    foreground_channels = [int(foreground[index : index + 2], 16) for index in (1, 3, 5)]
    background_channels = [int(background[index : index + 2], 16) for index in (1, 3, 5)]
    channels = [
        round(front * alpha + back * (1 - alpha))
        for front, back in zip(foreground_channels, background_channels)
    ]
    return "#" + "".join(f"{channel:02X}" for channel in channels)


def test_visible_text_tokens_meet_aa_on_documented_surfaces():
    tokens = _read("static/css/tokens.css")

    assert "--txt2:     var(--color-n-600);" in tokens
    assert "--txt3:     var(--color-n-550);" in tokens
    assert "--color-n-600:  #666666;" in tokens
    assert "--color-n-550:  #726D69;" in tokens
    assert "--color-dk-txt2:  #B8B1A8;" in tokens
    assert "--color-dk-txt3:  #9A948C;" in tokens
    assert "--ok-text:  #486A4D;" in tokens
    assert "--err-text: #974646;" in tokens
    assert "--warn-text: #8A5C1F;" in tokens

    light_pairs = {
        "#666666": ("#FFFFFF", "#FAFAF9", "#F4F2F0"),
        "#726D69": ("#FFFFFF", "#FAFAF9", "#F4F2F0"),
    }
    dark_pairs = {
        "#B8B1A8": ("#171512", "#201D18", "#241F1A"),
        "#9A948C": ("#171512", "#201D18", "#241F1A"),
    }
    for foreground, backgrounds in (light_pairs | dark_pairs).items():
        for background in backgrounds:
            assert _contrast_ratio(foreground, background) >= 4.5

    light_semantic = (
        ("#486A4D", "#6B8E6F", 0.14),
        ("#974646", "#B85C5C", 0.12),
        ("#8A5C1F", "#C4893A", 0.14),
    )
    for text_color, tint_color, alpha in light_semantic:
        for surface in ("#FFFFFF", "#FAFAF9", "#F4F2F0"):
            tinted_surface = _composite(tint_color, surface, alpha)
            assert _contrast_ratio(text_color, tinted_surface) >= 4.5

    dark_semantic = (
        ("#7FB385", "#7FB385", 0.14),
        ("#DC8080", "#D07070", 0.16),
        ("#D4A060", "#D4A060", 0.16),
    )
    for text_color, tint_color, alpha in dark_semantic:
        for surface in ("#171512", "#201D18", "#241F1A"):
            tinted_surface = _composite(tint_color, surface, alpha)
            assert _contrast_ratio(text_color, tinted_surface) >= 4.5

    for foreground, background in (
        ("#FFFFFF", "#6B5B4D"),
        ("#FFFFFF", "#486A4D"),
        ("#FFFFFF", "#974646"),
        ("#1A1714", "#C9A87A"),
        ("#1A1714", "#7FB385"),
        ("#1A1714", "#DC8080"),
    ):
        assert _contrast_ratio(foreground, background) >= 4.5

    forms = _read("static/css/components/forms.css")
    assert "opacity: 1;" in forms


def test_fonts_are_global_only_when_shared_by_ordinary_pages():
    tokens = _read("static/css/tokens.css")
    base = _read("templates/base.html")
    bean_detail = _read("templates/beans_detail.html")

    assert "fonts.googleapis.com" not in tokens
    assert base.count("fonts.googleapis.com/css2") == 1
    for global_family in ("DM+Mono", "Inter", "Raleway"):
        assert global_family in base
    for label_family in ("Barlow+Condensed", "Playfair+Display", "Roboto+Slab"):
        assert label_family not in base
        assert label_family in bean_detail
    assert "Raleway:wght@400;600;700;800;900" in base
    assert "Roboto+Slab:wght@300;400;500;600;700" in bean_detail


def test_management_and_live_target_tokens_stay_separate():
    tokens = _read("static/css/tokens.css")
    buttons = _read("static/css/components/buttons.css")
    forms = _read("static/css/components/forms.css")
    live = _read("static/css/screens/live-roasting.css")

    assert "--control-min:      44px;" in tokens
    assert "--control-live-min: 54px;" in tokens
    assert "min-height: var(--control-min);" in buttons
    assert "width: var(--control-min);" in buttons
    assert "min-height: var(--control-min);" in forms
    assert live.count("var(--control-live-min)") >= 5


def test_foundations_define_flat_grouping_and_reduced_motion():
    tokens = _read("static/css/tokens.css")
    base = _read("static/css/base.css")
    cards = _read("static/css/components/cards.css")

    for token in (
        "--manage-gap:",
        "--manage-section-gap:",
        "--manage-section-padding:",
        "--motion-fast: 140ms;",
        "--motion-base: 180ms;",
        "--ease-standard:",
    ):
        assert token in tokens
    assert ".surface-flat" in base
    assert ".flat-section-group" in cards
    assert "box-shadow: none;" in cards
    assert "@media (prefers-reduced-motion: reduce)" in tokens
    assert "animation-duration: 0.01ms !important;" in base
    assert "transition-duration: 0.01ms !important;" in base


def test_primary_navigation_uses_progressive_named_transitions():
    base_css = _read("static/css/base.css")
    nav_css = _read("static/css/components/nav.css")
    base_template = _read("templates/base.html")
    live_template = _read("templates/roast_live.html")

    container_rule = re.search(r"\.container\s*\{(?P<body>.*?)\}", base_css, re.DOTALL)
    assert container_rule
    assert "animation:" not in container_rule.group("body")

    assert "@view-transition" in nav_css
    assert "navigation: auto;" in nav_css
    assert "view-transition-name: app-navbar;" in nav_css
    assert "view-transition-name: app-content;" in nav_css
    assert "view-transition-name: active-nav-indicator;" in nav_css
    assert "translateY(-4px)" in nav_css
    assert "translateY(4px)" in nav_css
    assert "animation-duration: var(--motion-base);" in nav_css
    assert "::view-transition-group(root)," in nav_css
    assert "::view-transition-group(app-navbar)," in nav_css
    assert "::view-transition-group(app-content)," in nav_css
    stable_groups = re.search(
        r"::view-transition-group\(root\),(?P<selectors>.*?)\{(?P<body>.*?)\}",
        nav_css,
        re.DOTALL,
    )
    assert stable_groups
    assert "::view-transition-group(app-navbar)" in stable_groups.group("selectors")
    assert "::view-transition-group(app-content)" in stable_groups.group("selectors")
    assert "animation: none;" in stable_groups.group("body")
    assert "width: 32px;" in nav_css
    assert "@media (prefers-reduced-motion: reduce)" in nav_css
    assert "animation: none !important;" in nav_css

    assert base_template.count('aria-current="page"') == 2
    assert base_template.count('class="nav-active-indicator"') == 2
    assert 'data-nav-tab="roasts"' in base_template
    assert 'data-nav-tab="beans"' in base_template
    assert base_template.index('class="nav-context-actions"') < base_template.index('</ul>')
    assert ".nav-context-actions" in nav_css
    assert ".nav-context-actions .btn" in nav_css
    assert "navToggle.setAttribute('aria-expanded'" in base_template
    assert "no-route-transition" in live_template


def test_frontend_copy_uses_regular_hyphens_only():
    sources = list((ROOT / "templates").rglob("*.html"))
    sources.extend(
        path
        for path in (ROOT / "static/js").rglob("*.js")
        if not path.name.endswith(".min.js")
    )

    for source in sources:
        content = source.read_text(encoding="utf-8")
        content = re.sub(r"\{#.*?#\}|<!--.*?-->|/\*.*?\*/", "", content, flags=re.DOTALL)
        content = re.sub(r"^\s*//.*$", "", content, flags=re.MULTILINE)
        assert "—" not in content, source
        assert "–" not in content, source
