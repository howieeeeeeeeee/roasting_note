---
id: RN-0032
title: Remove blocking browser confirmation popups
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
tags: [ui, browser-control, confirmations]
---

# Remove blocking browser confirmation popups

## Description

Remove application-owned native browser confirmation popups so ordinary bean
and roast actions work without interrupting browser control. The user requested
this follow-up after manually dismissing popups during RN-0031 verification.

## Details

- Current behavior: synchronous `confirm()` / `window.confirm()` calls block
  purchase removal, bean archival, stock zeroing, draft completion/deletion,
  roast ending/archival, review deletion, and Settings cleanup. In the in-app
  browser, input commands stalled while the dialog API reported no active
  dialog; a person had to dismiss the browser popup before control resumed.
- Minimum change: remove redundant confirmation steps from ordinary actions.
  Removing a purchase row remains an unsaved form edit until Update Bean;
  archive, zero-stock, End Roast, and Complete Draft act from their existing
  clearly labelled controls. Preserve pending-button disabling, inline errors,
  stock correction history, stale-write protection, and repeat-action handling.
- Inventory every application-owned confirmation call, including inline HTML
  event handlers. Do not replace native confirmation calls with native alerts
  or prompts, or introduce a dialog framework or dependency.
- For irreversible review or bulk local-data deletion, expose scope and
  consequences in the page and use explicit in-page Delete/Cancel controls.
  Those controls must remain accessible to browser automation and keyboard
  users, with cancellation making no request. Bulk cleanup remains in Settings
  Advanced; do not widen the endpoint's permitted database or data scope.
- Guarded database synchronization already uses visible preflight, verified
  backup, and apply controls. Preserve that separate operational workflow and
  the CLI's run-specific confirmations; this ticket concerns browser popups.
- No undo framework, schema migration, archive restoration feature, or broader
  UI redesign is required. Implement this ticket separately from RN-0031.

## Acceptance Criteria

- [ ] Application actions use no native `confirm()`, `alert()`, or `prompt()`
  as a replacement confirmation mechanism, including inline template handlers.
- [ ] Purchase removal, zeroing, archive, End Roast, and Complete Draft work
  through the page without requiring a person to dismiss a browser dialog.
- [ ] Irreversible deletion has explicit scope and accessible in-page controls;
  cancellation has no side effect and duplicate clicks do not duplicate work.
- [ ] Stock accounting, lifecycle transitions, validation, visible failures,
  and guarded database-sync requirements retain their documented behavior.
- [ ] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [ ] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: ui-interaction, cross-workflow
- Browser verification level: full
- Automated tests to add or update: `tests/test_management_design_contracts.py`,
  `tests/test_design_contracts.py`, `tests/test_settings_sheet_contracts.py`,
  and `tests/test_api_contracts.py` for direct action/inline deletion contracts;
  retain accounting/lifecycle coverage in `tests/test_beans_api.py`,
  `tests/test_roasts_api.py`, and `tests/test_reviews_api.py`; verify cleanup
  isolation in `tests/test_e2e_runtime.py`. Use fake clients for destructive
  Settings routes. Add one focused source contract covering native popup calls
  in application JavaScript and template handlers.
- Browser E2E scenarios to add or update: `tests/e2e/README.md` Bean, Repeat
  purchases and inventory reconciliation, Live Roast, roast/review deletion,
  and Settings Advanced. Replace obsolete popup-dismissal steps with direct
  action or in-page Delete/Cancel steps. Verify keyboard operation, cancel,
  successful action, failed request, disabled pending controls, and continued
  browser control at desktop and mobile widths. Use isolated run markers;
  bulk-cleanup success requires a fake executor, never a real production purge.
- Required commands: focused pytest for the files above; `uv run pytest`;
  `uv run python -m tests.e2e.manage start --run-id rn-0032-confirmations-a`;
  `uv run python -m tests.e2e.manage cleanup --run-id rn-0032-confirmations-a`;
  `uv run python scripts/generate_issues_index.py`;
  `uv run python scripts/generate_issues_index.py --check`.
- Required browser evidence: action results and inline cancellation screenshots,
  exact stock checks, no native-dialog stalls, console/network findings,
  isolated runtime identity, and scoped cleanup in ignored
  `tests/e2e/artifacts/rn-0032-confirmations-a/summary.md`.
- Not applicable reason: None; the affected controls span critical inventory,
  live-roast, and Settings workflows.

## Documentation Impact

- `docs/features/beans-management.md` and `docs/features/live-roasting.md`:
  ordinary action behavior and removal of obsolete popup instructions.
- `docs/design/screens/bean-inventory.md`, `docs/design/screens/live-roasting.md`,
  `docs/design/screens/roast-detail.md`, and `docs/design/screens/settings.md`:
  action labels, in-page deletion/cancellation, focus, errors, and pending state.
- `tests/README.md` and `tests/e2e/README.md`: automated inventory and updated
  browser scenarios. Update API documentation only if route contracts change.

## Database Operations Impact

- Collections and local/online effects: existing bean/roast/review actions retain
  the selected database and current write semantics. Existing Settings cleanup
  remains restricted to its documented local scope. No new persistence shape.
- Migration or backfill: None.
- Expected sync direction: None; guarded mirror behavior is outside this change.
- Is an applied mirror part of delivery: No.
- Required backup/audit evidence: use mocks and isolated run data for verification;
  never purge production local data or apply a mirror as a test. If implementation
  changes database routes or services, read `docs/features/database-sync.md`,
  record a configured read-only sync forecast, and verify no backup payloads
  are tracked before resolution.

## Open Questions

- None blocking. The request authorizes creating this follow-up ticket; its
  implementation is a separate task.

## Related Files

- `static/js/bean-purchases.js`
- `static/js/live-roast/session.js`
- `static/js/settings-sheet.js`
- `templates/beans_detail.html`
- `templates/index.html`
- `templates/roast_detail.html`
- RN-0031: observed confirmation-tool stalls while verifying purchase history.
