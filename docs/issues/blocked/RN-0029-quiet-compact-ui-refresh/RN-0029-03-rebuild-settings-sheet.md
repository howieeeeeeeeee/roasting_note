---
id: RN-0029-03
title: Rebuild Settings as Accessible Sectioned Sheet
type: improvement
status: blocked
priority: high
created: 2026-08-20
resolved:
area: settings
parent: RN-0029
decisions: []
blocked_by: [RN-0029-01]
testing_policy: v1
tags:
  - settings
  - accessibility
  - responsive
  - sensor
  - database-sync
  - safety
---

# Rebuild Settings as Accessible Sectioned Sheet

## Description

Replace the tall all-in-one Settings modal with a viewport-bounded right-side
sheet organized into Sensor, Data, and Advanced sections. Preserve every
sensor, database, sync, and cleanup behavior while making the surface compact,
keyboard complete, and mobile-native.

## Details

- Current behavior: Settings stacks temperature-sensor configuration, database
  mode, sync preflight, and destructive cleanup in one roughly `802px` content
  column. The overlay needs about `898px` at `1024x768`, while mobile content
  reaches about `936px`; important controls fall below the fold.
- Shell: Open a fixed right-side sheet from the existing gear button. Desktop
  and tablet use a maximum width of `560px` and height of `100dvh`; below
  `768px`, Settings becomes a full-screen sheet. The underlying page does not
  scroll while open.
- Header: Use a sticky title row with a real close button. The selected section
  remains visible while the sheet body scrolls internally. Do not use a text
  multiplication sign as the only close control.
- Sections: Provide keyboard-operable Sensor, Data, and Advanced tabs or an
  equivalent single-select section control. Only the selected section is
  visible and focusable.
  - Sensor contains URL, Save, Test Connection, and connection status.
  - Data contains database mode plus all read-only or guarded sync states.
  - Advanced contains test-data cleanup and local-database cleanup inside a
    collapsed Danger Zone that is closed by default.
- Height contract: The sheet itself never exceeds the viewport. At
  `1024x768` and `1280x640`, default Sensor and Data states fit without outer
  page or overlay scrolling. Expanded sync, failure, audit, or Danger Zone
  content may scroll only inside the sheet body while the title and section
  navigation remain available.
- Dialog accessibility: Expose a labeled modal-dialog contract, contain focus,
  choose an intentional initial focus target, close on Escape when safe, and
  return focus to the gear button. Hidden sections are removed from keyboard
  order. Focus rings and status announcements remain visible in both themes.
- State preservation: Closing and reopening during ordinary settings use
  returns to the last selected section for the current page session. It must
  not erase active request, status, confirmation, restoration, or error state.
- RN-0028 coordination: Before implementation begins, rebase onto the guarded
  Settings-sync work if it has landed and add RN-0028 as a frontmatter blocker
  if it remains unfinished. Its preview, backup, apply, cancellation, resume,
  typed-confirmation, locality, fail-closed, and audit states must all map into
  the Data section without weakening any gate.
- Safety: Do not change endpoint methods, payloads, confirmation copy, local
  versus hosted availability, E2E exclusion, audit output, or destructive
  confirmation behavior. Moving a control does not authorize an operation.
- In scope: Settings markup, sheet/tabs CSS, focus and keyboard behavior,
  responsive layout, existing state placement, safe text rendering, automated
  contracts, full browser verification, and matching docs.
- Out of scope: new Settings features, API or database changes, an applied
  mirror, remote sync enablement, confirmation bypasses, a route change, or a
  redesign of other modals.

## Acceptance Criteria

- [ ] Settings opens from the existing gear as a right-side desktop/tablet
  sheet and a full-screen mobile sheet without moving or scrolling the page
  underneath it.
- [ ] Sensor, Data, and Advanced are keyboard-operable single-select sections;
  only the selected section is visible, announced, and focusable.
- [ ] Default Sensor and Data states fit within the sheet at `1024x768` and
  `1280x640` without outer page/overlay scrolling.
- [ ] Expanded content scrolls only inside the sheet body while the title,
  close button, and section control remain available.
- [ ] Advanced keeps the Danger Zone collapsed by default and retains both
  existing cleanup explanations, confirmations, button severity, and results.
- [ ] The close control is a real button; the sheet is labeled as a modal
  dialog, contains focus, handles Escape safely, and returns focus to Settings.
- [ ] Hidden sections cannot receive focus, and every request status or result
  continues to use an appropriate live-region announcement.
- [ ] Closing, reopening, and page-session section restoration do not erase or
  duplicate active Settings requests or their visible state.
- [ ] All RN-0022 and applicable RN-0028 sync safety, confirmation, audit,
  restoration, hosted/local, and E2E states remain complete in the Data section.
- [ ] Sensor save/test, database selection, preflight/sync, and cleanup routes,
  payloads, server behavior, and safe text construction remain unchanged.
- [ ] Light and dark modes pass contrast and focus-state requirements at
  `1440x900`, `1280x640`, `1024x768`, and `390x844`.
- [ ] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [ ] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: Update `tests/test_api_contracts.py` for modal-dialog labeling, real close button, Sensor/Data/Advanced relationships, hidden-section focus exclusion, live regions, safe text construction, and existing Settings controls; update `tests/test_design_contracts.py` for viewport-bounded sheet geometry, sticky header/section navigation, internal overflow, full-screen mobile fallback, focus styles, and reduced motion; retain or update `tests/test_database_sync_routes.py`, `tests/test_temperature_api.py`, and any RN-0028 web-sync tests to prove behavior and safety are unchanged; retain `tests/test_file_size_policy.py`
- Browser E2E scenarios to add or update: Replace or extend `tests/e2e/README.md` -> `Codex In-App-Browser Workflow` -> `Preflight And Fail-Closed Sync` and add `Quiet Compact UI` -> `Settings sheet`: open/close by mouse, keyboard, and Escape; verify focus containment/return and hidden-tab exclusion; save/test the sensor; inspect local/online database states; exercise every available preflight or guarded RN-0028 phase including failure/restoration; expand and cancel both Danger Zone confirmations; repeat at all required viewports and themes without performing a live mirror or destructive cleanup
- Required commands: `uv run pytest tests/test_api_contracts.py tests/test_design_contracts.py tests/test_database_sync_routes.py tests/test_temperature_api.py tests/test_file_size_policy.py`; run every focused RN-0028 web-sync test present after reconciliation; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0029-settings-sheet-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0029-settings-sheet-a`; `git diff --check`; `git ls-files db_backup 'db_backup/**'`
- Required browser evidence: Record run ID `rn-0029-settings-sheet-a`; save Sensor, Data, expanded-result, Advanced-collapsed, confirmation-cancelled, short-height, mobile, and dark-mode screenshots; record focus order/return, Escape behavior, viewport/overflow measurements, RN-0028 state coverage when present, console errors, failed network requests, zero applied-mirror activity, tracked-backup check, and cleanup in `tests/e2e/artifacts/rn-0029-settings-sheet-a/summary.md`
- Not applicable reason: None. Settings is a critical surface and the new section/dialog interactions require full workflow verification.

## Documentation Impact

- Rewrite `docs/design/screens/settings.md` for sheet anatomy, section states,
  viewport rules, focus behavior, dark mode, and RN-0028 state mapping.
- Update `docs/design/components/buttons.md` for the close control, selected
  section control, focus, and pressed states.
- Update `docs/design/components/cards-surfaces.md` for the side-sheet overlay
  and internal overflow recipe.
- Update `docs/design/foundations/spacing-layout.md` and `dark-mode.md` for
  viewport, responsive, contrast, and focus rules.
- Update `docs/features/temperature-sensor.md` from Settings-modal wording to
  the Sensor section without changing behavior.
- Update `docs/features/database-sync.md` from Settings-modal wording to the
  Data section and preserve every guarded operation contract.
- Update `tests/README.md` for rendered Settings contracts and
  `tests/e2e/README.md` for the full Settings sheet workflow.
- Conditional: update `docs/architecture/api-endpoints.md` only if the
  implementation diff changes an endpoint, which is currently out of scope.

## Database Operations Impact

None. Focused reads confirm this ticket reorganizes existing Settings controls
and presentation only. It changes no collection, document shape, persistence,
route, sync direction, migration, backfill, backup, audit, or applied-mirror
behavior. Automated and browser checks use existing fakes or the isolated E2E
database and must never run an applied mirror.

## Open Questions

- None. Sensor, Data, and Advanced are the approved sections; Danger Zone is
  collapsed; desktop/tablet use a right sheet and mobile uses full screen.

## Related Files

- `templates/base.html`
- `static/css/components/modals.css`
- `static/css/components/nav.css`
- `roastlogger/blueprints/settings.py`
- `tests/test_api_contracts.py`
- `tests/test_database_sync_routes.py`
- `tests/test_temperature_api.py`
- `tests/e2e/README.md`
- `docs/features/database-sync.md`
- `docs/features/temperature-sensor.md`
