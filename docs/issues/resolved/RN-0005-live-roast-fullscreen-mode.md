---
id: RN-0005
title: Live Roast Page - Fullscreen Mode
type: feature
status: resolved
priority: medium
created: 2026-01-16
resolved: 2026-01-16
area: live-roasting
parent:
decisions: []
blocked_by: []
tags:
  - fullscreen
  - tablet
  - ipad
---

# Live Roast Page - Fullscreen Mode

## Description

Add a fullscreen mode toggle for the live roasting page to optimize the interface for roasting on iPad Air (Safari). The fullscreen mode should reorganize the page layout to maximize visibility of critical information during active roasting sessions, with separate optimized layouts for portrait and landscape orientations.

## User Need

When roasting with an iPad Air, the current page layout includes navigation and other elements that take up screen space. A dedicated fullscreen mode would:

- Maximize space for the temperature chart
- Make current readings more prominent and easier to glance at
- Keep controls accessible but not intrusive
- Provide a cleaner, distraction-free roasting interface

## Requirements

### Fullscreen Button

- Add a button on the normal live roast page to enter fullscreen mode
- Button should be clearly labeled (e.g., "Fullscreen Mode" or icon)
- Clicking toggles the page into fullscreen layout

### Portrait Mode Layout

When in portrait orientation on iPad:

1. **Top Section - Current Readings** (1)
   - Display current time, temperature, and RoR
   - Large, easy-to-read text
   - Fixed position at top of screen

2. **Middle Section - Data Visualization** (3)
   - Place the Curve/Data tabs here
   - Should take up most of the screen space
   - Allow switching between chart view and data table

3. **Bottom Section - Controls** (1)
   - Control panel with fan/power controls and event buttons
   - Fixed position at bottom of screen
   - Keep all critical controls accessible

### Landscape Mode Layout

When in landscape orientation on iPad:

1. **Overall Structure**
   - Similar to current design but streamlined
   - Only show the three essential sections:
     - Current temperature readings
     - Control panel
     - Curve/Data tabs
   - Remove navigation bar and other non-essential elements

2. **Exit Button**
   - Place "Exit Fullscreen" button in top-right corner
   - Should be clearly visible but not intrusive
   - Clicking returns to normal page layout

### Target Device

- Primary device: iPad Air
- Primary browser: Safari, i will hide the toolbar of safari while using
- Should work on both portrait and landscape orientations

## Success Criteria

- [x] Fullscreen button visible on normal live roast page
- [x] Portrait mode displays all three sections in correct order (readings → chart → controls)
- [x] Landscape mode shows streamlined three-section layout
- [x] Exit fullscreen button appears in top-right corner (landscape mode)
- [x] Current readings (time, temp, RoR) are clearly visible in both orientations
- [x] All controls remain functional in fullscreen mode
- [x] Chart updates in real-time while in fullscreen mode
- [x] Easy to toggle between normal and fullscreen modes
- [x] Layout adapts properly when rotating iPad between portrait and landscape
- [x] No browser fullscreen API needed (pure layout changes)

## User Workflow

1. User opens live roast page on iPad
2. User clicks "Fullscreen Mode" button
3. Page reorganizes into optimized layout based on current orientation
4. User can roast with better visibility and less clutter
5. User clicks "Exit Fullscreen" to return to normal view

## Related Files

- `templates/roast_live.html` - Live roasting interface
- `static/css/style.css` - Styling for fullscreen layouts
- `static/js/roast-chart.js` - May need adjustments for layout changes

## Resolution

Implemented fullscreen mode with the following features:

### HTML Changes (`roast_live.html`)
- Added "Fullscreen" button with icon in page header
- Added "Exit Fullscreen" button (fixed position, top-right)
- Added fullscreen readings panel with large Time, Temp, and RoR displays
- Added IDs to key sections for JavaScript manipulation

### CSS Changes (`style.css`)
- Added fullscreen mode styles (~400 lines)
- Portrait mode: readings at top, chart in middle, controls fixed at bottom
- Landscape mode: readings bar at top, controls in left sidebar, chart on right
- Safe area insets for notched devices
- iPad-specific responsive adjustments

### JavaScript Changes
- `toggleFullscreen()`: Shows/hides navbar, footer, setup section; triggers layout
- `handleOrientationChange()`: Detects portrait/landscape and applies CSS classes
- `syncFullscreenDisplays()`: Syncs timer, temp, RoR to fullscreen panel
- Event listeners for resize and orientationchange

### Implementation Notes
- Pure CSS layout changes (no browser fullscreen API)
- Chart automatically resizes when entering/exiting fullscreen
- All controls remain functional in fullscreen mode
- Smooth transitions between modes
