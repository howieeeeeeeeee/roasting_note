---
id: RN-0027
title: Add Bean Stock Remaining Meter
type: improvement
status: resolved
priority: medium
created: 2026-08-20
resolved: 2026-08-20
area: bean-inventory
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags:
  - beans
  - inventory
  - stock
  - ui
---

# Add Bean Stock Remaining Meter

## Description

Turn the Beans inventory stock label into a compact two-tier indicator: an
exact remaining-stock pill with a separate thin meter beneath it. The meter
adds original-batch context without crowding the narrow Stock column with
consumed-weight or percentage text.

## Details

- Current behavior: Each Beans list row shows only the current signed
  `stock_grams` value in a centered pill, such as `300g`. The value does not
  show how much of the bean's original purchased weight remains.
- Approved composition: Keep the pill as the primary element and place a
  separate, 3–4px rounded progress track 4px beneath it. The pill reads
  `<signed stock_grams>g left`, such as `300g left`. The thin meter is a
  secondary visual cue, not part of the pill surface.
- Ratio: When `purchase_weight_grams` is a positive integer, compute
  `remaining_percent` as
  `clamp((stock_grams / purchase_weight_grams) * 100, 0, 100)`. The filled
  portion represents remaining stock and the unfilled portion represents the
  consumed or unavailable share. For an original `2000g` batch with `300g`
  left, the meter is 15% filled.
- Exceptional values: Preserve the exact signed stock value in the pill. A
  zero or negative balance renders an empty meter; stock above the purchase
  weight renders a full meter while the pill continues to show the uncapped
  amount. When purchase weight is missing, non-integer, zero, or negative,
  render the pill alone and omit the progressbar rather than inventing a
  ratio.
- Information density: Do not add visible consumed grams, original weight,
  fraction text, or a numeric percentage. The pill and thin meter must fit in
  the existing centered Stock cell without widening the 9% column or changing
  the table's fixed layout and narrow-screen horizontal-overflow behavior.
- Visual treatment: Preserve the current stock-pill typography, rounded
  shape, normal green treatment, and existing `.stock-low` treatment. Use the
  corresponding stock foreground color for the meter fill and a quiet neutral
  track; add no border, legend, icon, tooltip, gradient, animation, or left
  accent strip.
- Accessibility: Render a real `role="progressbar"` only when the positive
  purchase-weight baseline exists. Provide `aria-valuemin="0"`,
  `aria-valuemax="100"`, the clamped ratio in `aria-valuenow`, and concise
  `aria-valuetext` containing the remaining stock, original stock, and
  percentage. The visible pill remains readable without the meter.
- Existing behavior: Stock sorting continues to use raw `stock_grams`; row
  navigation, default out-of-stock filtering, **Show Out of Stock**, dark
  mode, and bean create/edit/detail behavior remain unchanged. This ticket
  adds no interaction, API route, stored field, stock-history entry, or
  database write.
- In scope: The Beans list Stock cell markup, its focused badge/table styles,
  ratio and fallback rendering, accessibility semantics, targeted browser
  verification, automated rendering contracts, and matching documentation.
- Out of scope: Showing the meter on bean detail or labels, displaying a
  consumed amount or numeric percentage, changing purchase or stock data,
  redefining low-stock thresholds, adding historical stock baselines, changing
  sorting/filtering, and redesigning other table columns or badges.
- Verification: Rendered-contract tests cover representative ratios and edge
  values; the full pytest suite passes; and a targeted Beans-list browser run
  verifies the approved compact layout, accessibility value, existing row
  navigation, responsive overflow, console/network state, and cleanup.

## Acceptance Criteria

- [x] A bean with `purchase_weight_grams: 2000` and `stock_grams: 300` renders
  `300g left` in the existing pill with a separate thin meter beneath it filled
  to 15%.
- [x] The Stock cell shows no visible consumed weight, original weight,
  fraction, or numeric percentage, and the meter is not fused into the pill.
- [x] Meter width is clamped to 0% for zero or negative stock and 100% for
  stock above the purchase weight while the pill preserves the exact signed,
  uncapped gram value.
- [x] A bean without a positive integer `purchase_weight_grams` renders its
  stock pill unchanged apart from the approved `left` copy and does not render
  a misleading progressbar.
- [x] Every rendered meter exposes the clamped percentage and descriptive
  remaining/original context through valid progressbar ARIA attributes.
- [x] The compact stack fits the existing Stock column in light and dark modes
  without widening the table, clipping the pill, obscuring another column, or
  breaking narrow-screen horizontal scrolling.
- [x] Existing low-stock styling, raw-stock sorting, out-of-stock filtering,
  and clickable-row navigation continue to behave as before.
- [x] No bean or roast document, API contract, synchronization behavior, or
  stock history is changed by rendering the indicator.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-visual
- Browser verification level: targeted
- Automated tests to add or update: `tests/test_api_contracts.py` for the Beans-list stock indicator markup and accessible ratio at 300/2000, zero and negative stock clamping, above-original clamping, missing/zero/negative purchase-weight fallback, signed pill copy, and preservation of the existing out-of-stock filter labels; `tests/test_file_size_policy.py` remains the policy check for the changed template, CSS, and documentation
- Browser E2E scenarios to add or update: Update `tests/e2e/README.md` -> `Codex In-App-Browser Workflow` -> `Bean` with a targeted **Bean stock remaining meter** scenario: create or edit the run-marked bean to an original purchase weight of `2000g` and current stock of `300g`, return to Beans, verify `300g left`, inspect the progressbar as 15%, confirm there is no visible consumption or percentage copy, sort the Stock column, open the bean through its row, and inspect the Stock cell at desktop and narrow widths; treat clipping, column overlap, broken horizontal scrolling, an incorrect accessible value, console errors, or failed network requests as failures
- Required commands: `uv run pytest tests/test_api_contracts.py tests/test_file_size_policy.py`; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0027-stock-meter-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0027-stock-meter-a`
- Required browser evidence: Record run ID `rn-0027-stock-meter-a`; save desktop and narrow-width screenshots showing the two-tier Stock cell; record the visible-copy, 15% progressbar, sorting, row-navigation, overflow, dark-mode, console-error, failed-network-request, and cleanup findings in `tests/e2e/artifacts/rn-0027-stock-meter-a/summary.md`
- Not applicable reason: None. Although the change is presentation-only, the dense fixed-width table cell, responsive overflow, calculated accessible value, and shared stock states warrant a focused browser check.

## Documentation Impact

- Update `docs/features/beans-management.md` to describe the Beans-list
  remaining-stock ratio, its `purchase_weight_grams` baseline, clamping, and
  missing-baseline fallback.
- Update `docs/design/screens/bean-inventory.md` with the approved two-tier
  Stock cell anatomy, compact spacing, visible-information limits, color
  treatment, accessibility semantics, and responsive constraints.
- Update `tests/README.md` to include the rendered stock-meter contracts in the
  automated test inventory.
- Update `tests/e2e/README.md` with the targeted Bean stock remaining-meter
  scenario and evidence expectations.

## Database Operations Impact

None. Focused repository reads confirm the indicator derives read-only display
state from existing `beans.stock_grams` and `beans.purchase_weight_grams`
fields. It adds no stored field, persistence behavior, route, migration,
backfill, synchronization, mirror, backup, or audit operation.

## Open Questions

- None. The finalized design uses a remaining-stock pill above a separate thin
  ratio meter, shows no visible consumed amount or percentage, and uses the
  existing purchase weight as the original-stock baseline.

## Resolution

- Added the Beans-list Stock-cell indicator without changing the page shell,
  table width, column definitions, navigation, sorting, filtering, or data
  behavior. The existing pill now uses signed `<grams>g left` copy and an
  optional separate remaining-stock meter.
- Added clamped ratio and accessibility rendering for positive integer
  purchase-weight baselines, including zero, negative, above-baseline, and
  missing/invalid-baseline contracts. Long signed values stay on one line;
  focused Stock-cell padding gives meter rows modest additional breathing room
  while keeping the meter close to the pill.
- Kept the meter within the existing 9% Stock column and improved the quiet
  neutral track so the light-mode fill/track contrast measures 3.29:1; dark
  mode also passes the graphical-object threshold.
- Targeted in-app-browser run `rn-0027-stock-meter-a` passed at desktop and
  narrow widths in light and dark modes. It verified `300g left`, 15% ARIA
  context, no visible ratio copy, raw-stock sorting, detail navigation,
  horizontal overflow, single-line `2500g left`, an empty warning/error
  console, and no observed failed requests.
- Follow-up run `rn-0027-stock-meter-b` verified the requested spacing tune in
  both themes: a 62.03px meter-row height and 3.99px pill-to-meter gap, with no
  surrounding layout change, console warning/error, or failed request.
- Scoped cleanup deleted one isolated E2E bean and left zero matching beans and
  roasts. Evidence is recorded under the ignored run artifact directory.
- Focused verification passed (`9 passed`) and the complete suite passed
  (`164 passed`). Feature, screen-design, automated-test, and browser-runbook
  documentation were updated. No database write, sync, backup, migration, or
  audit operation is part of this rendering-only change.

## Related Files

- `templates/beans_list.html`
- `static/css/components/badges.css`
- `static/css/components/tables.css`
- `tests/test_api_contracts.py`
- `tests/e2e/README.md`
- `docs/features/beans-management.md`
- `docs/design/screens/bean-inventory.md`
