---
id: RN-0001
title: Chart Visualization Fixes
type: bug
status: resolved
priority: high
created: 2025-01-09
resolved: 2025-01-10
area: charting
tags:
  - roast-detail
  - live-roasting
  - chart
---

# Chart Visualization Fixes

## Description

Multiple issues with the roast chart visualization on detail and edit pages.

## Issues Fixed

1. **Chart not visible on detail page**
   - Power/Fan timeline bars missing from roast_detail.html
   - Chart code was duplicated instead of shared

2. **Power/Fan bars not showing segments**
   - Bars were solid color instead of showing distinct segments when settings changed
   - No labels (P4, F9) to indicate current setting

3. **Event markers cut off**
   - Event marker labels (FC, SC, etc.) were cut off at top of chart
   - yAdjust was positioning labels outside visible area

4. **Event markers appearing in wrong order**
   - Clicking quick events showed markers in wrong positions
   - Root cause: Using category X-axis (string labels) instead of linear (numeric)

5. **RoR spikes making chart unreadable**
   - RoR values of 100+ at roast start distorted the chart
   - Solution: Filter to only plot RoR <= 30

6. **Dropdown menu not responding**
   - Edit/Delete dropdown on roast detail page was non-functional
   - Root cause: Malformed Jinja2 template (`{ {` instead of `{{`)

## Resolution

### Created Shared Chart Module
- New file: `static/js/roast-chart.js`
- Functions: `init()`, `initFromData()`, `addDataPoint()`, `addEventMarker()`
- Used by: roast_live.html, roast_detail.html, roast_edit.html

### Fixed Chart Configuration
- Changed X-axis from category to linear type
- Changed event marker yAdjust from -20 to 15
- Reduced chart height from 440px to 370px
- Added RoR filtering (only values <= 30)

### Fixed Template Syntax
- Corrected `{ {` to `{{` in roast_detail.html reviewsData

## Related Files

- `static/js/roast-chart.js` (created)
- `static/css/style.css`
- `templates/roast_detail.html`
- `templates/roast_edit.html`
- `templates/roast_live.html`
