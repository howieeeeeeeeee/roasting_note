# Settings Sheet

Settings is a viewport-bounded side sheet for sensor, data, and local
maintenance controls. Behavioral sync rules live in
[Guarded Database Sync](../../features/database-sync.md). The rendered shell is
in [templates/base.html](../../../templates/base.html), interaction behavior is
in [static/js/settings-sheet.js](../../../static/js/settings-sheet.js), and its
layout is in
[static/css/components/settings-sheet.css](../../../static/css/components/settings-sheet.css).

## Anatomy

Desktop and tablet use a right-aligned sheet no wider than `560px`. The sheet
fills `100dvh`, with three fixed layout rows:

1. A title row with a real Close Settings button.
2. A Sensor, Data, and Advanced single-select tab row.
3. One internally scrolling panel.

The overlay locks body scrolling. At widths below `768px`, the sheet fills the
screen with no outer radius or side border. Safe-area padding protects the
header on notched mobile devices.

## Dialog And Keyboard Contract

`#settingsDialog` uses `role="dialog"`, `aria-modal="true"`, and the
visible `#settingsTitle` label. The gear button exposes the dialog relationship
and expanded state.

When Settings opens:

- focus moves to the remembered section tab;
- the last section is restored from page-session storage;
- only the selected panel is rendered in the accessibility tree; and
- sensor, database, and active-run state load without clearing visible results.

Left Arrow, Right Arrow, Home, and End move and select section tabs. Tab and
Shift+Tab remain contained inside the sheet. Escape and overlay selection close
the sheet, body scrolling resumes, and focus returns to the control that opened
Settings. Closing does not cancel or reset an active request.

Any replacement sync confirmation receives focus only when Data is visible.
When Data is hidden, its controls remain unfocusable and no asynchronous result
may move focus into that panel.

## Sensor

Sensor contains:

- a visible Sensor URL label and input;
- Save and Test Connection actions; and
- a polite live status for load, save, connected, fault, and unavailable states.

Routes and retry behavior remain specified in
[Temperature Sensor](../../features/temperature-sensor.md).

## Data

Data contains two groups separated by one quiet divider.

### Database Connection

The Local and Online radios retain their existing route and values. Dedicated
E2E mode shows `local (roastlogger_e2e / <run-id>)` and disables Online.

### Guarded Database Sync

The section title remains **Guarded Database Sync**. Supporting text explains
that preview is first and direct local operation requires separate exact backup
and apply confirmations.

Two secondary buttons remain visible:

- **Preview Online → Local**, with the cloud-download icon;
- **Preview Local → Online**, with the cloud-upload icon.

Only one preflight may be active. While a request is pending, both buttons are
disabled, both show **Preflight running...**, and their labels and availability
are restored after success or failure.

`#syncPreflightResult` is a polite, atomic live region. A successful preflight
shows the run ID, sanitized source and destination, collection counts, complete
backup scope, guarded CLI command, audit path, and connection eligibility.

An eligible local preview adds:

- an empty text input labeled with the exact `BACKUP <run-id>` token;
- the token in selectable code styling; and
- **Create complete backup**.

A hosted or non-loopback preview shows **Guarded CLI only from this
connection** and no applied controls.

## Guarded Phase States

After complete backup verification, Data shows:

- run ID and direction;
- **Complete and verified**, or **Restored and re-verified** after reload;
- collection and document totals;
- verified manifest SHA-256 and ignored backup path;
- an empty input labeled with `APPLY <direction> <run-id>`; and
- separate Apply synchronization and Cancel run actions.

Reloading or reopening Settings calls the active-run endpoint. A valid
awaiting-apply run restores the same state and keeps both preview buttons
disabled. Cancellation reports `cancelled_after_backup`, the retained backup,
and its terminal audit. Success reports per-collection outcomes, aggregate
outcomes, and the applied audit path.

A stale apply gate clears only when the active endpoint reports no run and no
newer preflight has replaced it. Rejected apply or cancel requests render
inline beside the restored gate.

Backup failure, partial sync failure, interrupted state, corrupt state, and
audit recovery use the error treatment. Recovery-required state keeps preview
disabled, provides sanitized guidance, and never offers apply or automatic
retry. Audit persistence failure must not be described as recorded.

All server-provided values use `textContent` or text nodes. Confirmation
inputs disable autocomplete and spellcheck and retain an accessible label that
contains the required token.

## Advanced

Advanced begins with a collapsed native `details` disclosure named **Danger
Zone**. Opening it reveals the unchanged maintenance actions:

- Clean Up Test Data, including its existing confirmation and result counts.
- Clean Up Local DB, including both existing confirmations and danger severity.

Cleanup results appear in a visible polite status and in the global toast
region. The disclosure is closed on initial page load and is not automatically
opened when the Advanced tab is selected.

## Overflow And Short Viewports

The overlay and page never scroll while Settings is open. Only
`.settings-sheet-body` may scroll. The title and section tabs remain
available. At heights up to `680px`, header and section padding tighten while
all controls retain at least a `44px` target.

Default Sensor and Data content fit within the sheet at `1024x768` and
`1280x640`. Expanded sync results and Danger Zone content may require internal
scrolling.

## Color, Focus, And Motion

All surfaces consume semantic tokens, so light and dark modes preserve the same
hierarchy. Selected tabs use the primary token; success and error panels use
their semantic border and tint. Focus uses a visible `2px` primary outline
with offset on tabs, Close Settings, buttons, radios, and Danger Zone.

The overlay fade and sheet translation only run when the user has not requested
reduced motion. Reduced-motion mode is instant, and all animations are limited
to opacity and transform.

## E2E Safety State

Ordinary dedicated E2E mode keeps sync preflight visible but fails closed. A
click produces the existing prominent error and artifact-local intent audit
without initializing online state.

The full guarded interaction is enabled only with the explicit sync fake. It
exercises the same typed gates, restore, cancel, terminal, and recovery
rendering against ignored run artifacts and must never appear in an ordinary
E2E run.
