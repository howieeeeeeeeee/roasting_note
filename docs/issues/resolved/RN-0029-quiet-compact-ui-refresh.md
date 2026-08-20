---
id: RN-0029
title: Deliver Quiet Compact UI Refresh
type: epic
status: resolved
priority: high
created: 2026-08-20
resolved: 2026-08-20
area: design-system
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - design
  - ui
  - ux
  - navigation
  - settings
  - responsive
  - accessibility
  - motion
---

# Deliver Quiet Compact UI Refresh

## Description

Apply the approved Quiet Compact design direction across RoastLogger's
browse-and-manage surfaces. Make Roasts and Beans navigation feel continuous,
replace the tall Settings modal with a sectioned responsive sheet, and reduce
unnecessary vertical chrome without changing the live-roast instrument
workflow or application behavior.

## Details

### Approved Direction

- This epic records the user-selected Variant A, **Quiet Compact**: preserve
  the current information architecture, warm palette, dark-mode identity,
  top navigation, URLs, and familiar workflows while improving continuity,
  density, hierarchy, and accessibility.
- Design dials are `variance: 4`, `motion: 4`, and `density: 6`. Motion is
  restrained feedback for navigation and state changes, not decoration.
- The live-roast instrument layout, chart dominance, large critical controls,
  and active-roast interaction are protected. Shared navigation work may not
  reduce their dimensions or add content animation to the live screen.

### Audit Baseline

- Roasts and Beans use ordinary full-document links. The stable header is
  recreated while `.container` receives a new `fadeUp` animation on every
  page, so the active tab and content snap rather than read as one workspace.
  No View Transitions API or equivalent progressive enhancement exists.
- The Settings content is about `802px` tall. Its overlay needs about `898px`
  at a `1024x768` viewport, and the mobile content grows to about `936px`,
  placing destructive controls below the fold.
- The Add Bean form is about `1277px` tall inside a `1024x767` viewport. The
  `46px` controls are appropriately touch-friendly; stacked panel padding,
  dividers, and gaps create most of the avoidable height.
- The tertiary text token measures about `2.26:1` on the light surface and
  `1.89:1` on the dark surface. It is used for small table headings and other
  visible text that needs stronger contrast.
- Six font families are requested globally in `templates/base.html` and then
  requested again by `static/css/tokens.css`. Several are label-only faces
  that ordinary list and form pages do not need.
- Settings uses a clickable close span rather than a complete dialog contract.
  Focus containment, Escape handling, focus return, and hidden-section focus
  behavior must be explicit in the replacement.

### Outcome And Roadmap

1. `RN-0029-01` establishes contrast, density, surface, and font-loading
   foundations without changing the brand palette or live-roast sizing.
2. `RN-0029-02` makes primary navigation continuous with progressive,
   reduced-motion-aware cross-document transitions while keeping normal URLs.
3. `RN-0029-03` rebuilds Settings as an accessible right-side sheet with
   Sensor, Data, and Advanced sections and a full-screen mobile fallback.
4. `RN-0029-04` compacts Bean and Roast browse, detail, and edit screens while
   preserving field names, validation, table behavior, and DOM order.

`RN-0029-01` lands first. The remaining children depend on its shared tokens
and component rules. `RN-0029-03` must also be reconciled with `RN-0028` when
that guarded Settings-sync record lands on `main`; RN-0028's safety stages,
typed confirmations, restoration, and failure states govern over visual
convenience. `RN-0029-04` must preserve the RN-0027 Bean stock-meter contract
if that work lands first.

### Scope Boundaries

- In scope: UI foundations, top-level navigation continuity, Settings shell
  and information architecture, browse/manage density, semantic dialog and
  focus behavior, responsive layouts, dark-mode parity, documentation, and
  proportional automated/browser regression coverage.
- Out of scope: a SPA rewrite, HTMX or another navigation framework, route or
  navigation-label changes, API or database behavior, icon-family migration,
  printable label/sticker redesign, live-roast control rearrangement, and any
  applied database mirror.
- Existing loading, empty, error, confirmation, preflight, and destructive
  states remain available and truthful. The refresh changes their layout and
  presentation only unless a child explicitly records otherwise.

## Acceptance Criteria

- [x] All four child tickets are resolved and their declared documentation,
  automated tests, browser scenarios, and evidence are complete.
- [x] Roasts and Beans retain their URLs and top-navigation labels while the
  navbar remains visually stable and the selected-tab indicator and main
  content transition as one restrained state change.
- [x] Reduced-motion users receive an instant, stable navigation update with
  no opacity, translation, or shared-element choreography.
- [x] Settings is a viewport-bounded, keyboard-complete sectioned sheet; its
  default Sensor and Data states do not require outer-page scrolling at
  `1024x768` or `1280x640`, and mobile uses a full-screen layout.
- [x] Browse-and-manage forms and detail screens use less vertical chrome,
  keep actions reachable, preserve minimum `44px` interactive targets, and
  collapse to one logical column below `768px`.
- [x] Normal visible text, placeholders, table headings, and inactive
  navigation text meet WCAG AA contrast in both light and dark modes.
- [x] Ordinary pages no longer request the complete printable-label font set
  twice, and label rendering retains every documented font preset.
- [x] Live roasting preserves chart dominance, existing setup and event
  interactions, monospaced readings, critical target sizes, and sensor states.
- [x] No route, form field name, data model, database operation, synchronization
  contract, destructive confirmation, or analytics-sensitive label changes.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-visual, ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: Add `tests/test_design_contracts.py` for contrast-token, font-loading, reduced-motion, transition, responsive-sheet, semantic-dialog, and management-layout contracts; update `tests/test_api_contracts.py` for rendered navigation, Settings, Bean form, Roast form, and protected live-roast markup; retain `tests/test_file_size_policy.py` for every changed source and documentation file
- Browser E2E scenarios to add or update: Add `tests/e2e/README.md` -> `Codex In-App-Browser Workflow` -> `Quiet Compact UI` as the aggregate full workflow: switch repeatedly between Roasts and Beans using links plus Back/Forward, verify the stable navbar and reduced-motion fallback, exercise every Settings section and its existing Sensor/Data/Advanced states, complete Bean create/edit/detail/list and Roast edit/detail checks, then smoke-test the live-roast shell for protected sizing and behavior at `1440x900`, `1280x640`, `1024x768`, and `390x844` in light and dark modes
- Required commands: `uv run pytest tests/test_design_contracts.py tests/test_api_contracts.py tests/test_file_size_policy.py`; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0029-quiet-compact-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0029-quiet-compact-a`; `git diff --check`
- Required browser evidence: Record run ID `rn-0029-quiet-compact-a`; save before/after-navigation, Settings section, compact Bean/Roast form, narrow-screen, dark-mode, and protected live-roast screenshots; record motion and reduced-motion observations, viewport overflow measurements, keyboard/focus results, console errors, failed network requests, and cleanup results in `tests/e2e/artifacts/rn-0029-quiet-compact-a/summary.md`
- Not applicable reason: None. The refresh changes shared visual foundations and interactions across multiple workflows, including the critical Settings surface, so full browser verification is required.

## Documentation Impact

- Update `docs/design/principles.md` with stable-workspace continuity and the
  separate density rules for roasting-critical versus management surfaces.
- Update `docs/design/foundations/color.md`, `typography.md`,
  `spacing-layout.md`, and `dark-mode.md` for the approved tokens, scoped font
  delivery, density rules, motion fallback, and contrast parity.
- Add `docs/design/components/navigation.md`; update
  `docs/design/components/buttons.md`, `cards-surfaces.md`, and `forms.md` for
  focus, active, surface, sheet, and compact form recipes.
- Update `docs/design/screens/settings.md`, `bean-inventory.md`, and
  `roast-detail.md` for the approved layouts and protected behavior.
- Update `docs/design/README.md` for the new navigation component and any new
  cross-links.
- Update `docs/features/database-sync.md` and
  `docs/features/temperature-sensor.md` only for the Settings location and
  interaction wording; behavior and safety contracts remain unchanged.
- Update `tests/README.md` for new automated design contracts and
  `tests/e2e/README.md` for the full Quiet Compact workflow.
- Conditional: update `docs/architecture/tech-stack.md` only if implementation
  changes font delivery, adds a dependency, or introduces a runtime capability
  beyond native CSS and browser APIs.

## Database Operations Impact

None. Focused reads confirm this epic changes presentation, layout, focus,
navigation motion, and documentation only. It adds no stored field, MongoDB
write, migration, backfill, sync direction, mirror, backup, or audit operation.
The guarded Settings-sync behavior remains governed separately by RN-0022 and
RN-0028.

## Open Questions

- None. Variant A is finalized: retain the top navigation and warm brand,
  introduce restrained progressive transitions, use a sectioned Settings
  sheet, compact management surfaces, and protect live roasting.

## Resolution

- Delivered the selected Quiet Compact direction across shared foundations,
  primary navigation, Settings, and Bean/Roast management screens while
  preserving routes, form payloads, guarded-sync behavior, and the live-roast
  instrument workspace.
- The aggregate in-app-browser run `rn-0029-quiet-compact-a` passed the light,
  dark, desktop, short-height, tablet, and mobile workflow. It verified
  navigation/history fallback, Settings keyboard and responsive behavior,
  compact forms and details, stock compatibility, and live-roast isolation.
- Browser feedback was incorporated before resolution: contextual Add Bean and
  New Roast labels remain readable, and global toasts use one neutral border
  without a colored left rail.
- The in-app browser exposed partial View Transition support, so the complete
  feature gate selected clean native navigation without console errors.
  Reduced-motion behavior was verified by the static design contract because
  the harness could not emulate that preference.
- Guarded-sync checks used only the artifact-local fake executor and recorded
  `database_access: false`; no real mirror or destructive cleanup ran. Scoped
  E2E cleanup deleted one test roast and one test bean and left zero run records.
- The complete automated suite passed (`213 passed`), JavaScript and diff
  checks passed, and no backup payload is tracked.

## Related Files

- `templates/base.html`
- `templates/index.html`
- `templates/beans_list.html`
- `templates/beans_form.html`
- `templates/beans_detail.html`
- `templates/roast_edit.html`
- `templates/roast_detail.html`
- `templates/roast_live.html`
- `static/css/tokens.css`
- `static/css/base.css`
- `static/css/components/nav.css`
- `static/css/components/modals.css`
- `static/css/components/forms.css`
- `static/css/components/cards.css`
- `tests/e2e/README.md`
