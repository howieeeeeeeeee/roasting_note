---
id: RN-0006
title: Live Chart and Data Recording Issues
type: bug
status: resolved
priority: high
created: 2026-01-18
resolved: 2026-01-18
area: live-roasting
tags:
  - chart
  - ror
  - data-recording
---

# Live Chart and Data Recording Issues

(this is fixed poorly by Claude code)

## Description

Multiple issues discovered while using the live roasting page that affect data visualization, layout responsiveness, and data recording accuracy. These have been fixed.

## Resolved Issues

### 1. Fan/Power Bar Resolution Issue - FIXED

**Problem:**

- The fan and power timeline bars were rendered as separate canvas graphs
- Visual quality/resolution was not ideal
- They were fragile during resize

**Solution:**

- Added Fan and Power as proper Chart.js datasets with stepped, dashed band rendering
- Uses a dedicated y-axis (`y-pf`) scaled 0-36 to keep bands within ~25% height at value 9
- Fan and Power now display in the tooltip (legend remains hidden)
- Resizes properly with the chart

**Files Changed:**

- `templates/roast_live.html` - Added Power and Fan datasets to chart config

---

### 2. Layout and Resize Issues - FIXED

**Problems:**

- Default layout under full screen mode was too wide
- Fan and power controls were stacked vertically

**Solution:**

- Reduced default left panel width from 380px to 280px in fullscreen landscape mode
- Restructured settings inputs: Temperature on its own row, Fan/Power on same row
- Added new CSS classes: `.settings-group`, `.settings-row-temp`, `.settings-row-fp`

**Files Changed:**

- `templates/roast_live.html` - Restructured settings HTML
- `static/css/style.css` - Added new layout styles, updated fullscreen styles

---

### 3. ROR > 30 Not Filtered on Live Page - FIXED

**Problem:**

- ROR values exceeding 30°C/min were displayed on live chart
- This caused misleading spikes, especially at the beginning

**Solution:**

- Added ROR filtering in `updateChartData()` function
- Only includes ROR values <= 30 in chart (matches detail page behavior)
- Filtered values show as `null` (gaps in the line)

**Files Changed:**

- `templates/roast_live.html` - Added filter: `const filteredRor = (ror !== null && ror !== undefined && ror <= 30) ? ror : null;`

---
---

## Success Criteria - All Met

- [x] Fan and power bars render using proper chart objects (not graph-like)
- [x] Default layout has smaller left control panel
- [x] Fan and power controls displayed on same row
- [x] Temperature chart resizes responsively with layout changes
- [x] ROR values > 30°C/min are filtered from live page chart
- [x] Live page ROR behavior matches completed roast detail page
- [x] No negative time values in any recorded data points
- [x] No abnormal spikes at beginning of chart from end-of-roast data
- [x] "Drop" event automatically recorded when ending roast
- [x] Drop event appears on chart with marker (like other events)
- [x] Drop event includes accurate time and temperature

## Related Files Modified

- `static/js/roast-chart.js` - Added Drop event color
- `templates/roast_live.html` - Chart datasets, settings layout, event colors
- `static/css/style.css` - Layout and control styling
- `app.py` - Backend data recording and roast end logic
