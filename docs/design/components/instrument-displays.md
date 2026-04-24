# Instrument Displays

The family of large, glanceable numeric readouts and the event buttons that sit next to them. These components carry the "instrument panel" feel of the live roasting screen.

## Top-bar Tiles (`.tb-tile`)

The canonical instrument readout. Used in a row of four on the [live roasting screen](../screens/live-roasting.md): Elapsed, Temperature, RoR, Since FC.

```
┌──────────┐
│   TEMP   │  ← .tb-label  (0.5625rem, uppercase, 0.12em tracking, text-light)
│  221°C   │  ← .tb-value  (DM Mono, 2.5rem, primary-color)
│          │
└──────────┘
   88px tall, 2rem side padding, right-border between tiles
```

**Key rules**

- Value uses **DM Mono** — fixed-width digits so numbers don't jitter as they tick.
- Colour is `var(--primary-color)` — reading *is* the primary content.
- Label is always uppercase, heavily tracked (`0.12em`), at 75% opacity. Small on purpose: the value is the hero.
- Unit suffix (`.tb-unit`) inherits DM Mono at `0.9375rem`, in `--text-light`.
- Tiles separate with `1px solid var(--border-color)` on the right edge. No top/bottom borders — the top-bar container provides those.

## FC Elapsed Tile

A conditional variant of `.tb-tile` that appears only after First Crack Start is logged. The value uses `.tb-value-fc` (`2rem`, slightly smaller) and a red sub-line (`.tb-sub`, DM Mono `0.6875rem`, `--danger-color`) marking development time.

Show/hide is driven by JS in [templates/roast_live.html](../../../templates/roast_live.html) — the `#fcElapsedTile` element is toggled when `fcStartTime` is set.

## Stepper Control (`.stepper-control`)

Used for Fan and Power in the live controls bar and for Settings rows.

```
┌─────────────────────┐
│  [−]    7    [+]    │  ← .btn-stepper + .stepper-value + .btn-stepper
└─────────────────────┘
   44px tall, bg-color, border, 6px radius
```

**Key rules**

- Fixed **44px** height — this is the floor for a touch-friendly target on a tablet.
- `.stepper-value` uses fixed-width type (historically Courier New; new code should use DM Mono) at `1.5rem`, weight 700.
- +/- buttons are borderless `.btn-stepper` that use Material icons at `1.25rem`.
- Hover tints the +/- button background with `--border-color`.

## Legacy Panels (`.timer-panel`, `.temp-panel`, `.panel-value`)

The older instrument style used before the top-bar redesign. Still present in fullscreen mode and non-live pages. `.panel-value` uses `3rem` monospace in `--primary-color`, with a smaller `.unit` subtitle. Newer code should prefer `.tb-tile` for consistency.

## Event Buttons (`.live-ev-btn`, `.event-btn-compact`)

The row of five event buttons below the chart on the live screen (Y, FC, FC–, SC, SC–).

- Layout: `display: grid; grid-template-columns: repeat(5, 1fr);` — always one row, always equal width.
- Dual-class (`.live-ev-btn.event-btn-compact`): the first class carries the new styling, the second preserves the original JS selector hooks.
- **States**:
  - Idle: neutral card background, dark-mode aware border.
  - Hover: border + text shift to `--primary-color`, background picks up a translucent accent tint (dark mode only).
  - **Fired**: `.fired` class — green tint (`rgba(127,179,133,0.15)` background, `var(--success-color)` border + text). Stays fired after click to give visual roast history.
- Font weight 600, size `0.875rem`.

## Dark Mode

All instrument components consume palette tokens (`--primary-color`, `--bg-color`, `--border-color`). The dark-mode rules in [static/css/style.css](../../../static/css/style.css) (`body.dark-mode .stepper-control`, `.timer-panel`, `.temp-panel`, `.live-ev-btn`) explicitly swap the background to `--bg-color` so the instrument surfaces sit slightly *below* the card background in dark mode — creating a subtle inset feel that reinforces the "instrument embedded in a panel" read.
