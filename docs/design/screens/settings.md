# Settings Modal

The Settings modal combines temperature-sensor configuration, database mode,
guarded database-sync preflight, and destructive local cleanup controls.
Behavioral sync rules live in
[Guarded Database Sync](../../features/database-sync.md).

## Database Sync Preflight Section

The section title is **Database Sync Preflight**. Supporting text must state
that the actions preview the guarded CLI operation and never modify either
database.

Two secondary buttons remain visible:

- **Preview Online → Local**, with the cloud-download icon;
- **Preview Local → Online**, with the cloud-upload icon.

They use existing `.btn.btn-secondary` styling from
[`static/css/components/buttons.css`](../../../static/css/components/buttons.css)
and the `.sync-buttons` responsive row in
[`static/css/components/modals.css`](../../../static/css/components/modals.css).

## Active State

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
- exact guarded CLI command; and
- persisted audit-record path.

A safely recorded preflight failure displays its credential-free error and
audit path. An audit persistence failure is visually prominent and must not be
described as fully recorded. Content is constructed with `textContent` and text
nodes so endpoint labels cannot inject markup.

## Responsive Behavior

The existing flex-wrap layout allows buttons to wrap at narrow widths. The
result panel uses `overflow-wrap: anywhere` for long run IDs, paths, and CLI
commands. No new breakpoint or design token is introduced.
