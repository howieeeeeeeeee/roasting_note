---
id: RN-0029-04
title: Compact Browse and Edit Screens
type: improvement
status: resolved
priority: medium
created: 2026-08-20
resolved: 2026-08-20
area: design-system
parent: RN-0029
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - beans
  - roasts
  - forms
  - responsive
  - layout
  - accessibility
---

# Compact Browse and Edit Screens

## Description

Reduce unnecessary vertical chrome across Bean and Roast browse, detail, and
edit screens. Keep data density, field contracts, and touch targets intact
while making actions reachable and short-height layouts more efficient.

## Details

- Current behavior: The Add Bean form is about `1277px` tall at a
  `1024x767` viewport. Its three stacked panels measure roughly `490px`,
  `381px`, and `288px`; repeated `28px` padding, panel gaps, heading dividers,
  and card shells create most of the avoidable scroll.
- Management shell: Apply the Quiet Compact container, page-heading, action,
  and static-section recipes to Roasts and Beans lists, Bean add/edit/detail,
  and Roast edit/detail. Keep the top navigation and contextual actions from
  RN-0029-02.
- Forms: At `1024px+`, use a deliberate responsive grid that places compatible
  groups side by side and makes efficient use of width. Keep labels above
  fields, the logical DOM order, existing field names, helper/error placement,
  validation, and at least `44px` targets. Below `768px`, collapse to one
  column in the same logical order.
- Actions: Keep primary Save/Add and Cancel actions reachable through a
  viewport-aware sticky action row on long forms. It may not cover content,
  trap focus, or hide validation errors; print styles and short pages remain
  natural.
- Static grouping: Replace nested or repetitive static cards with the shared
  flat grouping recipe where elevation communicates no hierarchy. Preserve
  clear section names and sparse separators.
- Lists and tables: Keep the Roasts and Beans table information density,
  columns, sorting, filtering, row navigation, horizontal-overflow behavior,
  empty states, and contextual actions. Do not convert operational tables into
  decorative cards.
- Detail screens: Use compact responsive data clusters and section spacing
  while preserving record titles, reviews, stock history, roast curves,
  notes, action ordering, and print behavior.
- RN-0027 coordination: If the Bean stock remaining meter lands first, retain
  its two-tier Stock cell, accessible progressbar, fixed-column width,
  sorting, low-stock style, and responsive-overflow contract.
- Live-roast protection: `templates/roast_live.html`, instrument displays,
  event controls, chart layout, polling, and fullscreen modes are out of scope.
- Also out of scope: form field removal/reordering, copy or nav-label changes,
  API/data changes, label or sticker modal redesign, cards for table rows, and
  new frontend dependencies.

## Acceptance Criteria

- [x] Bean add/edit and Roast edit use available desktop/tablet width to reduce
  stacked panel height while preserving logical DOM order and field labels.
- [x] All form controls retain at least `44px` targets, labels above fields,
  visible helper/error text, keyboard order, autofill names, and validation.
- [x] Long forms keep Save/Add and Cancel reachable in a sticky action row that
  does not cover the final field, validation message, or mobile safe area.
- [x] At widths below `768px`, every multi-column form and detail cluster
  becomes one logical column with no horizontal page scrolling.
- [x] At `1280x640` and `1024x768`, compact headings, sections, and actions use
  materially less vertical chrome than the audit baseline.
- [x] Roasts and Beans tables retain their columns, sorting/filtering, row
  navigation, contextual actions, empty states, and narrow-screen overflow.
- [x] RN-0027 stock-meter markup and behavior remain intact if present; this
  ticket does not redesign or widen the Stock cell.
- [x] Bean and Roast detail screens preserve reviews, histories, charts,
  notes, print output, and existing action ordering.
- [x] Light/dark hierarchy, contrast, focus, hover, active, loading, empty, and
  error states remain complete at all required viewports.
- [x] Live-roast normal/fullscreen geometry, target sizes, chart, sensor states,
  and interactions are unchanged.
- [x] No API, route, field name, form payload, database shape, persistence,
  synchronization, or printable-output behavior changes.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-visual, ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: Update `tests/test_design_contracts.py` for management-grid breakpoints, `44px` target minimums, sticky action offset/safe-area rules, one-column mobile collapse, table overflow preservation, and live-roast exclusions; update `tests/test_api_contracts.py` for rendered form section/order/action hooks, table semantics, empty states, and RN-0027 Stock markup when present; retain `tests/test_beans_api.py` and `tests/test_roasts_api.py` as unchanged form/API behavior regressions plus `tests/test_file_size_policy.py`
- Browser E2E scenarios to add or update: Extend `tests/e2e/README.md` -> `Quiet Compact UI` -> `Browse and edit density`: complete Bean add/edit/detail/list and Roast edit/detail flows at desktop, short-height tablet, and mobile widths; verify sticky actions, focus/validation visibility, one-column collapse, table sorting/filtering/row actions/overflow, empty states, dark mode, RN-0027 Stock compatibility when present, and protected live-roast geometry
- Required commands: `uv run pytest tests/test_design_contracts.py tests/test_api_contracts.py tests/test_beans_api.py tests/test_roasts_api.py tests/test_file_size_policy.py`; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0029-management-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0029-management-a`; `git diff --check`
- Required browser evidence: Record run ID `rn-0029-management-a`; save Bean and Roast list/form/detail screenshots at `1440x900`, `1280x640`, `1024x768`, and `390x844` in light and dark modes; record form/page height comparisons, sticky-action and focus results, validation visibility, table/RN-0027 behavior, protected live-roast measurements, console errors, failed network requests, and cleanup in `tests/e2e/artifacts/rn-0029-management-a/summary.md`
- Not applicable reason: None. The ticket changes shared responsive form and action interactions across Bean and Roast workflows, so full browser verification is required.

## Documentation Impact

- Update `docs/design/foundations/spacing-layout.md` with management-shell,
  short-height, grid, mobile-collapse, and safe-area rules.
- Update `docs/design/components/forms.md` with compact grouping, DOM-order,
  sticky-action, validation, and responsive recipes.
- Update `docs/design/components/cards-surfaces.md` with static flat-group usage
  on management pages.
- Update `docs/design/screens/bean-inventory.md` for list, form, detail, and
  RN-0027 compatibility layouts.
- Update `docs/design/screens/roast-detail.md` for compact edit/detail grouping
  and protected chart/review/history behavior.
- Update `tests/README.md` for new rendered/layout contracts and
  `tests/e2e/README.md` for the full Browse and edit density workflow.

## Database Operations Impact

None. Focused reads confirm this ticket changes responsive markup, CSS,
presentation, focus layout, tests, and design documentation only. Existing
forms submit the same names and values to the same routes. No collection,
schema, persistence, migration, backfill, synchronization, backup, audit, or
applied-mirror behavior changes.

## Open Questions

- None. Compact the browse/manage surfaces, keep `44px` targets and native
  document/form behavior, preserve tables, and leave live roasting unchanged.

## Resolution

- Added responsive management-only grids, compact flat detail clusters, and
  safe-area-aware sticky Save/Cancel actions while preserving logical source
  order, labels, validation, field names, payloads, print behavior, and mobile
  one-column fallback.
- Retained operational tables, internal narrow-screen overflow, RN-0027 Stock
  markup, route behavior, detail content, and the untouched live-roast template.
- The parent aggregate browser run created, edited, and inspected an isolated
  Bean and Roast across tablet and mobile layouts. It verified reachable
  actions, visible validation, no page overflow, light/dark hierarchy, stock
  presentation, detail grids, and protected live controls.
- Management static contracts, unchanged Bean/Roast API regressions, and the
  complete `213 passed` suite succeeded. Scoped cleanup left no run records.

## Related Files

- `templates/index.html`
- `templates/beans_list.html`
- `templates/beans_form.html`
- `templates/beans_detail.html`
- `templates/roast_edit.html`
- `templates/roast_detail.html`
- `templates/roast_live.html`
- `static/css/base.css`
- `static/css/components/forms.css`
- `static/css/components/cards.css`
- `static/css/components/tables.css`
- `tests/test_design_contracts.py`
- `tests/test_api_contracts.py`
- `tests/e2e/README.md`
