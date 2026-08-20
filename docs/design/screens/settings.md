# Settings Modal

The Settings modal combines temperature-sensor configuration, database mode,
guarded database sync, and destructive local cleanup controls.
Behavioral sync rules live in
[Guarded Database Sync](../../features/database-sync.md).

## Guarded Database Sync Section

The section title is **Guarded Database Sync**. Supporting text explains that
preview is always first and direct local operation requires separate exact
backup and apply confirmations.

Two secondary buttons remain visible:

- **Preview Online → Local**, with the cloud-download icon;
- **Preview Local → Online**, with the cloud-upload icon.

They use existing `.btn.btn-secondary` styling from
[`static/css/components/buttons.css`](../../../static/css/components/buttons.css)
and the `.sync-buttons` responsive row in
[`static/css/components/modals.css`](../../../static/css/components/modals.css).

## Preview Active State

Only one preflight may be active. While a request is pending:

- both buttons are disabled;
- both show the spinning sync icon and **Preflight running...**;
- additional click calls return without issuing a request; and
- both original labels and enabled states are restored after success or
  failure.

This prevents ambiguous overlapping audit intent.

## Result Panel

`#syncPreflightResult` is an `aria-live="polite"` panel below the buttons. It
uses `.sync-preflight-result`, design tokens, and existing `.status-success` or
`.status-error` semantic colors.

A recorded successful preflight displays:

- run ID;
- sanitized source and destination role/host/database;
- source and destination collection counts;
- complete destination backup scope;
- exact guarded CLI command;
- persisted preflight-audit path; and
- whether this connection may continue in Settings.

An eligible local preview adds a labeled text input, the exact
`BACKUP <run-id>` token in selectable code styling, and **Create complete
backup**. The token is never prefilled. A hosted or non-loopback preview shows
**Guarded CLI only from this connection** and no applied controls.

## Backup And Apply States

The backup request is synchronous. While it runs, the preview controls remain
disabled. The next state appears only after complete-manifest and payload
verification and shows:

- run ID and direction;
- **Complete and verified** (or **Restored and re-verified** after reload);
- collection/document totals, verified manifest SHA-256, and ignored backup
  path;
- exact `APPLY <direction> <run-id>` token and an empty text input; and
- separate **Apply synchronization** and **Cancel run** actions.

Reloading the page or reopening Settings calls the active-run endpoint. A
valid awaiting-apply run restores this same state and keeps both preview
buttons disabled. Cancellation reports `cancelled_after_backup`, its retained
backup, and terminal audit. Success reports named per-collection outcomes,
aggregate outcomes, and the applied audit path. A cancellation whose terminal
audit needs recovery stays in the error treatment and never receives the
success toast.

If the active endpoint reports no run after this tab displayed a stale apply
gate, Settings clears that gate and re-enables previews without overwriting a
new preflight started during the lookup. A rejected apply or cancel request is
shown inline beside the restored gate. When a focused phase control is
replaced, focus moves to the next confirmation input or the terminal/status
result so keyboard operators do not fall back to the document.

Backup failure, partial sync failure, and audit recovery use the error color
and show only sanitized failure plus the available audit/recovery path.
Interrupted, corrupt, or inconsistent saved state displays **Recovery
required**, keeps preview disabled, and directs the operator to inspect ignored
artifacts; it never offers apply or automatic retry.

A safely recorded preflight failure displays its credential-free error and
audit path. An audit persistence failure is visually prominent and must not be
described as fully recorded. All server-provided labels, tokens, results, and
paths are inserted with `textContent` or text nodes so they cannot inject
markup. Confirmation inputs disable autocomplete and spellcheck and have an
explicit accessible label containing the required token.

## Responsive Behavior

The existing flex-wrap layout allows preview and phase actions to wrap at
narrow widths. Confirmation gates use a single-column grid; action buttons may
wrap. The result panel and selectable token use `overflow-wrap: anywhere` for
long run IDs and paths. No new breakpoint or design token is introduced.

## E2E Safety State

In dedicated E2E mode, the database label includes
`local (roastlogger_e2e / <run-id>)` and the Online radio is disabled. Sync
preflight buttons remain visible so the fail-closed RN-0022 contract can be
verified: a click produces the existing prominent error result and an
artifact-local intent audit, without initializing or accessing online state.

The full sync interaction is enabled only when the harness is started with its
explicit sync-fake option. Results are visibly simulated but exercise the same
typed gates, restore, cancel, terminal, and recovery rendering against ignored
run artifacts. The fake state must never appear in an ordinary E2E run.
