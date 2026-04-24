# Live Roasting Screen — Design

**Feature:** `templates/roast_live.html`  
**Branch:** `feature/live-roast-redesign`  
**Status:** Ready for review

---

## Problem

The original layout used a two-column grid (left panel: timer + controls, right panel: chart + log). On a tablet propped next to the roaster this caused three pain points:

- Controls (Fan/Power/events) were in the left column, far from the thumb when holding the tablet
- The chart was only ~2/3 of the available width, and competed with a tab bar
- The setup section was always visible, eating vertical space during the roast

## Decision: Top Bar Layout

Move the four key readings (Timer, Temp, RoR, Since FC) into a fixed horizontal bar at the top. The chart takes all remaining vertical space. Controls live in a compact strip at the bottom — within thumb reach from either side of the tablet.

```
┌──────────────────────────────────────────────────────────────┐
│  Bean: Ethiopia Yirgacheffe  ·  250g  ·  22°C  55%   ● Live │  ← setup bar (38px)
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

---

## Components

### Setup Bar (`.setup-bar`)
- Height: 38px, always visible
- Shows bean name, green weight, ambient temp/humidity, live indicator chip
- No changes from original — already well-designed

### Top Bar (`.live-topbar`)
- Height: 88px, `flex-shrink: 0`
- Four metric tiles: **Elapsed · Temperature · Rate of Rise · Since FC**
- The "Since FC" tile (`#fcElapsedTile`) is hidden until First Crack Start is logged, then shown automatically
- End Roast button lives in `.tb-end` (right-aligned, auto margin-left)
- Font: `DM Mono` for all numeric values — gives instrument-panel feel, consistent digit widths

### Chart Area (`.live-chart-area`)
- `flex: 1`, `min-height: 380px`
- Canvas is `position: absolute; inset: ...` so it fills 100% of the container at all times
- Chart.js with `maintainAspectRatio: false` — responds to container resize
- **Development time zone**: shaded box annotation from FC Start → current time (chartjs-plugin-annotation)
- **Event markers**: vertical dashed lines for Yellowing, FC Start, etc.
- Colors are dark-mode aware via `getChartColors()` — see [dark-mode.md](./dark-mode.md)

### Controls Bar (`.live-controls-bar`)
- Event buttons strip: 5 buttons in a CSS grid (`repeat(5, 1fr)`)
  - Use `.live-ev-btn` + `.event-btn-compact` (dual class — new style, original JS selector)
  - `.fired` class applied on click (green tint, stays fired for visual history)
- Input strip: Fan stepper · Power stepper · Note input · Log Event button
  - Steppers reuse existing `.stepper-control` / `.btn-stepper` / `.stepper-value` classes
  - `#temperature` input kept as `type="hidden"` — JS uses it as a fallback value

---

## JavaScript Changes

All existing IDs and event listeners are preserved. Changes are additive:

### `getChartColors()`
New helper function. Checks `document.body.classList.contains('dark-mode')` and returns a colour map. Called inside `initChart()` when building dataset configs.

```javascript
function getChartColors() {
    const dark = document.body.classList.contains('dark-mode');
    return {
        temp:   dark ? '#D4895A' : '#6B5B4D',
        tempBg: dark ? 'rgba(212,137,90,0.15)' : 'rgba(107, 91, 77, 0.1)',
        // ...
    };
}
```

### FC Elapsed Tile
`updateTimer()` now also updates `#fcElapsedTile` (show/hide) and `#fcElapsedValue` (text) whenever `fcStartTime` is set. The tile is also shown immediately when the FC Start event button is tapped.

### Dark Mode Listener
```javascript
window.addEventListener('darkmodechange', function () {
    if (roastChart) {
        roastChart.destroy();
        roastChart = null;
        initChart();
    }
});
```
Triggered by `base.html` when the user toggles dark mode. Rebuilds the chart with the correct colour palette.

---

## What Was Removed

| Removed | Reason |
|---|---|
| Two-column `.roast-panels` grid | Replaced by top bar + full-width chart |
| Left panel timer/temp/RoR sections | Moved to top bar tiles |
| "Log Event" section with visible temp input | Temp input hidden (auto-filled from sensor); controls in bottom strip |
| Curve / Log tab bar on right panel | Log tab removed from main view — events visible as chart annotations |

> **Note:** Fullscreen mode (`#fullscreenReadings`, `#fsControlsBar`) is **unchanged** in this PR. It still works as before. Fullscreen redesign is a separate task.

---

## Open Questions / Next Steps

- [ ] Redesign fullscreen mode to match the new layout
- [ ] Add a slide-out event log panel (swipe up from bottom) for reviewing logged data without leaving the roast view
- [ ] Consider larger tap targets for Fan/Power steppers on smaller tablets
- [ ] Test on actual iPad with the sensor connected
