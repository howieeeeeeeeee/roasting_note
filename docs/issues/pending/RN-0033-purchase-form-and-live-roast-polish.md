---
id: RN-0033
title: Polish purchase entry and restore readable live-roast metrics
type: improvement
status: pending
priority: high
created: 2026-09-15
resolved:
area: ui
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags: [beans, purchases, forms, live-roasting, fullscreen, accessibility]
---

# Polish purchase entry and restore readable live-roast metrics

## Description

Make bean purchase entry feel consistent with the rest of the form, with taller
fields, better spacing, compact removal, and a clear add action. Restore the
fullscreen time-since-first-crack display, align live measurements despite sensor
status changes, and name an untitled new roast from the selected bean.

## Details

### Current behavior and evidence

- User screenshots dated 2026-09-15 at 19:43:16 and 19:48:45 show shallow native
  purchase fields, an oversized Remove purchase control, a left-aligned Add
  purchase button, an unnecessarily full-width stock-correction field, and a
  Label Color shell taller than the adjacent Supplier field.
- The 19:51:15 screenshot shows the bean detail Purchase History table touching
  the **Add or edit purchases** button, with no visible vertical gap.
- Purchase inputs in `templates/partials/bean_purchase_row.html` sit directly
  inside labels instead of the usual styled `.form-group` structure. Reuse the
  existing form treatment rather than adding a separate visual system.
- `fullscreen.js` mirrors the legacy `fcTimeDisplay` into `fsFcTimeDisplay`,
  while the active timer updates `fcElapsedValue`. Fullscreen therefore does
  not show the current development time. Session boot also needs to restore
  the first-crack reference from existing recorded timings when resuming.
- Both live temperature layouts put sensor status below the value, changing
  the temperature block's height relative to Time/Elapsed and RoR.
- Draft setup already autosaves the roast title and selected bean. Bean option
  text includes an availability suffix; that suffix must not enter the title.

### Purchase form and Label Color

- Give date, weight, and total-price fields the same inset surface, typography,
  border, focus treatment, and control height as ordinary bean fields. Increase
  their height from the thin native inputs in the screenshot; retain native
  date and numeric input behavior. Use the existing control/spacing tokens.
- Add clear vertical gaps between the section hint, purchase rows, list action,
  and stock area. Keep rows quiet and readable, with aligned labels and inputs;
  avoid stretching short values across excessive widths on large screens.
- Place a wide, clearly labeled **Add purchase** button below the purchase list,
  aligned to its bottom-right edge. It should be wider than the removal action,
  not span the whole desktop form. Appending still focuses the new date field.
- Make **Remove** a compact secondary button within each row, with an accessible
  name identifying purchase removal. Reduce visual width while preserving the
  project's minimum touch target.
- Interpret "double confirm" as two deliberate clicks: **Remove** opens a
  small in-page confirmation for that row; **Confirm removal** removes it from
  the unsaved form. Include **Cancel**, identify the affected date/weight when
  present, and explain that the stock change applies only when the form is
  saved. Do not use native `confirm()`, `alert()`, or `prompt()` dialogs.
  Cancellation preserves all entered values and restores focus to Remove;
  confirmation moves focus to a sensible remaining control. Repeated activation
  must not remove a different row. Keep confirmation local to the selected row.
- Put **Correct stock to (grams)** and its input side by side in a compact,
  vertically centered row. Give the input the same height as the other fields;
  constrain its width to suit a gram count instead of filling the panel. Keep
  Current stock readable above and the explanation below. Preserve the blank
  default and automatic purchase accounting. Apply the same layout to Opening
  stock on create; stack only when needed at narrow widths.
- Match the Label Color wrapper's outer height and vertical alignment to the
  adjacent Supplier input. Fit its swatch and hex value inside that height;
  retain the compact width, native color picker, helper text, and focus state.
- Verify add/edit, multiple rows, 390px mobile, desktop, and light/dark modes
  without clipping, horizontal form overflow, or hidden save actions.

### Purchase History spacing on bean detail

- Add a clear vertical gap between the Purchase History table and **Add or edit
  purchases**. Use existing spacing tokens and consistent separation between
  the heading, table, action, and following content; the table border and button
  border must not touch. Keep the action visually associated with its history.
- Verify empty, single-row, and multiple-row histories at desktop and 390px
  widths in light/dark modes. Preserve table alignment, scrolling, and values.

### Live and fullscreen readings

- Show an explicitly labeled **Since FC** elapsed counter in fullscreen after
  First Crack Start, in `MM:SS` with second-by-second updates. Use the same
  recorded first-crack origin and clock as the normal view; do not introduce
  another timer or polling loop. Before FC, hide the counter or show an explicit
  unset state rather than a fabricated elapsed value.
- Entering/exiting fullscreen, portrait/landscape changes, and reloading a
  started roast after FC retain the correct counter. A failed FC event request
  must not leave a new, unsaved development-time origin on screen. Ending the
  roast stops elapsed updates as it does today.
- Move the compact sensor-state badge to the right of the temperature number
  and unit in both normal and fullscreen views. Keep Time/Elapsed, Temperature,
  and RoR number baselines aligned. Reserve enough space for **Live**, **Retrying**,
  **Stale Ns**, **Offline**, and **Sensor fault** so transitions do not shift the
  metric row. At narrow widths, reflow deliberately without overlap or hiding
  either the value or status; preserve readable text beyond color alone.
- Preserve sensor freshness rules, temperature/RoR values, events, chart,
  roasting controls, stock timing, and the existing polling cadence.

### Automatic naming for a new roast

- The user's reference to a new bean and an untitled name is interpreted as
  the **New Roast / Setup** flow: when selecting a bean while Roast Name is
  blank or the default **Untitled Roast** (also accept **Untitled**, ignoring
  surrounding whitespace/case), fill the last two whitespace-separated words
  of the bean's actual name. For example, **Guji Hambela Bishan Wate** becomes
  **Bishan Wate** and **Central Valley Volcan Azul Alejo Castro Reserve Villa
  Sarchi** becomes **Villa Sarchi**.
- Use the structured bean name, excluding `(Ng available)` and other display
  metadata. Trim/collapse whitespace; preserve spelling, case, and punctuation.
  A one-word bean name uses that word. An empty selection does not rename.
- Preserve a custom title, including a user's edit after autofill. Once an
  initial non-placeholder title has been filled, selecting another bean leaves
  it alone unless the user clears or resets it to the placeholder.
- Persist through the existing setup autosave/start payload. Reloading the
  draft retains the title, and starting immediately after selection must keep
  it. Do not rename historical, started, or completed roasts in bulk.

### Scope and related work

- Build on RN-0031 purchase history and RN-0032 nonblocking interactions. This
  request refines purchase removal with an explicit in-page second click while
  retaining RN-0032's prohibition on native browser dialogs. Do not restore
  confirmations on unrelated actions.
- Use existing templates, styles, and JavaScript modules; no new dependency,
  schema, inventory algorithm, or broad fullscreen redesign is needed.
- This is a planning record only. Implementation and its feature/design/test
  documentation belong in the subsequent implementation branch.

## Acceptance Criteria

- [ ] Purchase controls match standard bean-field height and styling; vertical
  spacing, compact Remove, and bottom-right wide Add purchase match the request.
- [ ] Remove requires an in-page confirm action; cancellation preserves the row,
  confirmation edits only that row, and only Save changes stored stock/history.
- [ ] Stock label/input share a compact horizontal row and consistent control
  height; Label Color aligns with Supplier without excess wrapper height.
- [ ] Bean detail Purchase History has clear vertical spacing around the table
  and its Add or edit purchases action, with no touching borders at any width.
- [ ] Normal and fullscreen Since FC counters agree, advance each second, and
  survive fullscreen toggling and resumed/reloaded roasts without false starts.
- [ ] Sensor status sits beside the temperature value and all three readings
  remain aligned across status changes, orientations, and supported widths.
- [ ] Selecting a bean fills only a blank/default draft title with its last two
  name words; custom titles survive changes, autosave, reload, and immediate start.
- [ ] Existing purchase accounting, validation/stale-save handling, sensor
  behavior, and roast lifecycle continue to pass regression verification.
- [ ] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [ ] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-visual, ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: `tests/test_management_design_contracts.py`
  for scoped form markup, removal confirmation semantics, and native-popup
  prohibition; `tests/test_api_contracts.py` for raw bean-name metadata and
  fullscreen/readout hooks; add `tests/test_live_roast_ui.py` with focused
  coverage for title derivation/preservation and first-crack restore/display
  behavior using the existing lightweight test approach. Retain regression
  coverage in `tests/test_beans_api.py` and `tests/test_roasts_api.py` for stock,
  setup persistence, start, and timing events. Exercise client interactions in
  the browser rather than relying solely on source-string assertions.
- Browser E2E scenarios to add or update: `tests/e2e/README.md` -> `Bean`,
  `Repeat purchases and inventory reconciliation (Full)`, `Popup-free actions
  and inline deletion (Full)`, and `Live Roast`. Add a named scenario **Purchase
  form, draft naming, and fullscreen readings (Full)**. Cover empty/multiple
  rows, removal cancel/confirm followed by form cancel/save, invalid and stale
  saves retaining values, stock correction, color picker, keyboard focus,
  bean-detail history/action spacing for empty/single/multiple-row histories,
  custom/placeholder/one-word titles, autosave/reload/immediate start, FC before
  and during fullscreen, resume after FC, failed FC recording, sensor failure
  and recovery, and end/save with unchanged inventory accounting.
- Required commands: `uv run pytest tests/test_management_design_contracts.py
  tests/test_api_contracts.py tests/test_live_roast_ui.py tests/test_beans_api.py
  tests/test_roasts_api.py`; `uv run pytest`;
  `uv run python -m tests.e2e.manage start --run-id rn-0033-polish-a`;
  `uv run python -m tests.e2e.manage cleanup --run-id rn-0033-polish-a`;
  `uv run python scripts/sync_database.py --direction local-to-online --dry-run`;
  `git ls-files db_backup 'db_backup/**'`;
  `uv run python scripts/generate_issues_index.py`;
  `uv run python scripts/generate_issues_index.py --check`.
- Required browser evidence: isolated runtime identity and run ID
  `rn-0033-polish-a`; form, inline confirmation, aligned Label Color/stock,
  bean-detail Purchase History and its separated edit action,
  normal/fullscreen metrics before/after FC, and sensor-state screenshots at
  desktop and actual 390 CSS-pixel widths in light/dark modes; tablet
  portrait/landscape fullscreen checks; timestamped Since FC comparisons,
  saved-title and exact stock assertions; console/network findings and scoped
  cleanup in ignored `tests/e2e/artifacts/rn-0033-polish-a/summary.md`.
- Not applicable reason: None. The combined request changes inventory-form
  interaction and draft/live-roast behavior across screens, so full coverage
  means the affected workflows, not unrelated Settings or cleanup features.

## Documentation Impact

- `docs/features/beans-management.md`: two-step in-page purchase removal and
  preserved save/cancel/stock semantics.
- `docs/design/screens/bean-inventory.md`: purchase layout, removal/focus,
  bottom-right add action, stock correction, color alignment, bean-detail history
  spacing, and responsive states.
- `docs/features/live-roasting.md`: default draft naming, Since FC restoration,
  fullscreen parity, and sensor status placement.
- `docs/design/screens/live-roasting.md` and
  `docs/design/components/instrument-displays.md`: aligned readings, adjacent
  status badge, fullscreen counter, and narrow/orientation behavior.
- `docs/design/components/forms.md`: bean-specific control-height/color and
  compact stock-row guidance; keep broad shared form contracts unchanged.
- `tests/README.md` and `tests/e2e/README.md`: focused automated inventory and
  durable scenarios, replacing obsolete immediate-removal steps.
- Conditional: `docs/architecture/api-endpoints.md` only if setup/timing API
  contracts change. No schema or navigation changes are planned.

## Database Operations Impact

- Collections and local/online effects: user-selected bean edits still use the
  existing `beans` save path; inferred draft names persist in the existing
  `roasts.title` through setup autosave/start. FC restoration reads recorded
  timings. Selected local/online mode and ordinary write rules stay unchanged.
- Migration or backfill: None; no schema changes or historical renaming.
- Expected sync direction: no new sync behavior; compatibility evidence uses
  the existing read-only `local-to-online` forecast.
- Is an applied mirror part of delivery: No.
- Required backup/audit evidence for resolution: read
  `docs/features/database-sync.md` before implementation, record a configured
  read-only dry run or endpoint limitation, and verify no `db_backup/` files
  are tracked. Verification uses fixtures and isolated run-marked data only;
  no production data rewrite, applied mirror, or migration is needed.

## Open Questions

- None blocking. Naming refers to new-roast setup as stated above, and double
  confirmation means Remove followed by an explicit in-page confirmation.

## Related Files

- `templates/beans_form.html`
- `templates/beans_detail.html`
- `templates/partials/bean_purchase_row.html`
- `static/js/bean-purchases.js`
- `static/css/screens/management.css`
- `static/css/components/forms.css`
- `templates/roast_live.html`
- `static/js/live-roast/session.js`
- `static/js/live-roast/fullscreen.js`
- `static/css/screens/live-roasting.css`
- `static/css/screens/live-fullscreen.css`
- RN-0031: repeated purchase history and inventory invariants.
- RN-0032: browser-native popup removal and in-page interactions.
