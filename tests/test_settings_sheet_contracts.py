"""Static contracts for the accessible responsive Settings sheet."""

from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_settings_sheet_markup_exposes_labeled_dialog_and_section_tabs(client):
    html = client.get("/").get_data(as_text=True)
    settings_html = html.split('id="settingsModal"', 1)[1].split("<main", 1)[0]

    assert 'id="settingsButton"' in html
    assert 'aria-haspopup="dialog"' in html
    assert 'aria-controls="settingsModal"' in html
    assert 'aria-expanded="false"' in html
    assert 'id="settingsDialog" role="dialog"' in html
    assert 'aria-modal="true" aria-labelledby="settingsTitle"' in html
    assert 'id="settingsCloseButton" type="button"' in html
    assert 'aria-label="Close Settings"' in html
    assert 'role="tablist" aria-label="Settings sections"' in html

    for section in ("Sensor", "Data", "Advanced"):
        section_key = section.lower()
        assert f'id="settingsTab{section}"' in html
        assert f'aria-controls="settingsPanel{section}"' in html
        assert f'data-settings-section="{section_key}"' in html
        assert f'id="settingsPanel{section}" role="tabpanel"' in html
        assert f'aria-labelledby="settingsTab{section}"' in html
        assert f'data-settings-panel="{section_key}"' in html

    assert 'id="settingsPanelData" role="tabpanel"' in html
    assert 'data-settings-panel="data" hidden' in html
    assert 'data-settings-panel="advanced" hidden' in html
    assert '<details class="settings-danger">' in html
    assert '<details class="settings-danger" open>' not in html
    assert 'id="syncPreflightResult" class="sync-preflight-result" role="status"' in html
    assert 'id="settingsActionStatus" role="status"' in html
    assert "modal-close" not in settings_html
    assert "&times;" not in settings_html


def test_settings_sheet_script_contains_complete_keyboard_and_state_cycle():
    script = _source("static/js/settings-sheet.js")

    assert 'sessionStorage.setItem(SETTINGS_SECTION_KEY, section)' in script
    assert 'panel.hidden = panel.dataset.settingsPanel !== selected' in script
    assert 'event.key === "ArrowRight"' in script
    assert 'event.key === "ArrowLeft"' in script
    assert 'event.key === "Home"' in script
    assert 'event.key === "End"' in script
    assert 'event.key === "Escape"' in script
    assert 'event.key === "Tab"' in script
    assert "containSettingsFocus(event)" in script
    assert "settingsPreviousFocus.focus()" in script
    assert 'document.body.classList.add("settings-sheet-open")' in script
    assert 'document.body.classList.remove("settings-sheet-open")' in script
    assert "if (settingsActiveSyncLookup)" in script
    assert "&& !syncRequestActive" in script
    assert "focusVisibleSyncControl(input)" in script
    assert '!settingsOverlay.hidden && panel && !panel.hidden' in script


def test_settings_sheet_css_is_viewport_bounded_and_responsive():
    css = _source("static/css/components/settings-sheet.css")

    assert ".settings-sheet-overlay:not([hidden])" in css
    assert "justify-content: flex-end" in css
    assert "width: min(100%, 560px)" in css
    assert "height: 100dvh" in css
    assert "max-height: 100dvh" in css
    assert "grid-template-rows: auto auto minmax(0, 1fr)" in css
    assert ".settings-sheet-body" in css
    assert "overflow-y: auto" in css
    assert "overscroll-behavior: contain" in css
    assert "body.settings-sheet-open { overflow: hidden; }" in css
    assert "@media (max-width: 767px)" in css
    assert "@media (max-height: 680px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert ".settings-tab:focus-visible" in css
    assert ".db-option input:focus-visible + .db-option-label" in css
