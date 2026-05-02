# Live Roasting Screen — Design

**Template:** [templates/roast_live.html](../../../templates/roast_live.html)
**Behaviour / API / lifecycle:** [docs/features/live-roasting.md](../../features/live-roasting.md)

The flagship screen of the app. Optimised for a tablet propped next to a roaster, used one- or two-handed, glanced at while physically operating the roaster.

## Problem the Layout Solves

The original layout used a two-column grid (left: timer + controls, right: chart + log). This caused three pain points:

- Controls (Fan/Power/events) were in the left column, far from the thumb when holding the tablet.
- The chart was only ~2/3 of the available width, and competed with a tab bar.
- The setup section was always visible, eating vertical space during the roast.

## Layout: Top-Bar

```
┌──────────────────────────────────────────────────────────────┐
│  Bean: Ethiopia Yirgacheffe  ·  250g  ·  22°C 55%   ● Live   │  ← setup bar (38px)
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│ 08:12    │  221°C   │ +5.0°/m  │ 01:12    │   [End Roast]   │  ← top bar (88px)
│ Elapsed  │  Temp    │  RoR     │ Since FC │                  │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│                                                               │
│                    ROAST CURVE CHART                          │  ← flex: 1
│              (temperature + RoR + dev zone)                   │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  [ Y ]  [ FC ]  [ FC– ]  [ SC ]  [ SC– ]                    │  ← controls bar
│  Fan [−]7[+]  Power [−]5[+]  Note…         [ Log Event ]    │
└───────────────────────────────────────────────────────────────┘
```

The four key readings are fixed in a horizontal bar at the top. The chart takes all remaining vertical space. Controls live in a compact strip at the bottom — within thumb reach from either edge of the tablet.

## Regions

### Setup Bar (`.setup-bar`)

- Height: 38px, always visible.
- Shows bean name, green weight, ambient temp/humidity, live indicator chip.
- Minimal styling — this is reference info, not action.

### Top Bar (`.live-topbar`)

- Height: **88px**, `flex-shrink: 0`.
- Four metric tiles: **Elapsed · Temperature · Rate of Rise · Since FC** — see [../components/instrument-displays.md](../components/instrument-displays.md#top-bar-tiles-tb-tile).
- The "Since FC" tile (`#fcElapsedTile`) is hidden until First Crack Start is logged, then shown automatically.
- The Temperature tile includes a compact sensor-state line under the numeric
  value. Normal state reads `Live`; transient failures read `Retrying`; failures
  older than 5 seconds read `Stale`; unavailable hardware reads `Offline` or
  `Sensor fault`.
- **End Roast** button lives in `.tb-end` (right-aligned via `margin-left: auto`). Uses `.btn-lg` + `.btn-danger`.

### Draft Manual Completion

Draft roasts expose a header action labeled **Set to Completed**. It uses the
shared secondary button recipe and sits beside **Fullscreen**, outside the live
top-bar controls so the roasting interaction remains unchanged once a roast has
started. The action is hidden for started and completed roasts, and the
confirmation copy states that only lifecycle metadata changes.

### Chart Area (`.live-chart-area`)

- `flex: 1`, `min-height: 380px`.
- Canvas is `position: absolute; inset: 0.5rem 1rem 0.375rem` so it fills 100% of the container at all times.
- Chart.js with `maintainAspectRatio: false` — responds to container resize.
- **Development time zone**: shaded box annotation from FC Start → current time (via `chartjs-plugin-annotation`).
- **Event markers**: vertical dashed lines for Yellowing, FC Start, etc.
- Colours are dark-mode aware via `getChartColors()` — see [../foundations/dark-mode.md](../foundations/dark-mode.md#chart-colours).

### Controls Bar (`.live-controls-bar`)

- **Event buttons row**: 5 buttons in `repeat(5, 1fr)` grid (`.live-ev-btn.event-btn-compact`). Fired state persists for visual history. See [../components/instrument-displays.md](../components/instrument-displays.md#event-buttons).
- **Input strip**: Fan stepper · Power stepper · Note input · Log Event button.
- Steppers use the shared `.stepper-control` / `.btn-stepper` / `.stepper-value` classes — 44px tall, DM Mono value.

## Dark Mode

All regions consume `var(--card-bg)` and `var(--border-color)`. The chart swaps its palette on `darkmodechange` (see [../foundations/dark-mode.md](../foundations/dark-mode.md)). Toggle via the moon icon in the navbar; preference persisted in `localStorage` under `roast-dark`.

## What Was Removed in the Redesign

| Removed | Reason |
|---|---|
| Two-column `.roast-panels` grid | Replaced by top bar + full-width chart |
| Left-panel timer/temp/RoR sections | Moved to top-bar tiles |
| "Log Event" section with visible temp input | Temp input hidden (auto-filled from sensor); controls in bottom strip |
| Curve / Log tab bar on right panel | Log tab removed — events visible as chart annotations |

**Not changed:** fullscreen mode (`#fullscreenReadings`, `#fsControlsBar`) uses its own layout. See [Fullscreen Mode](#fullscreen-mode) below.

## Fullscreen Mode

Separate layout, triggered from the navbar. Two flavours driven by device orientation:

- **Landscape** (`.fullscreen-landscape`): left panel with instrument tiles, right panel with the chart. At ≥ 768px the left panel is `400px` wide; at ≥ 1024px it widens to `420px`.
- **Portrait** (`.fullscreen-portrait`): instrument row on top, chart below.
- The fullscreen temperature readout mirrors the same sensor-state line as the
  top bar so stale/offline state remains visible while roasting fullscreen.
- Safe-area insets (`env(safe-area-inset-*)`) applied for notched devices.
- Fullscreen redesign to match the new top-bar layout is a pending item (see [Open Items](#open-items)).

## Open Items

- [ ] Redesign fullscreen mode to match the new top-bar layout.
- [ ] Slide-out event log panel (swipe up from bottom) for reviewing logged data without leaving the roast view.
- [ ] Larger tap targets for Fan/Power steppers on smaller tablets.
- [ ] Test on actual iPad with the sensor connected.
