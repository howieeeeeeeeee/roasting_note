# Issues - RESOLVED

All issues below have been addressed:

## Fixed Issues

1. **[FIXED] Chart sharing across pages**
   - Created shared `static/js/roast-chart.js` module
   - Power/Fan timeline bars now appear on roast_detail.html and roast_edit.html (same as roast_live.html)
   - All three pages use the same `RoastChart` object for consistency

2. **[FIXED] Power/Fan bars with colored segments and labels**
   - Implemented `detectSegments()` to identify when settings change
   - Implemented `drawSegmentedTimelineBar()` with:
     - Distinct colored segments for each setting value (1-9)
     - Power: Red gradient (light to dark)
     - Fan: Cyan/teal gradient (light to dark)
     - Labels like "P4" or "F9" displayed on segments wider than 20px
     - Borders between segments for visual clarity

3. **[FIXED] Chart height for event markers**
   - Increased `.chart-container-large` height from 400px to 440px (later reduced to 370px for compact layout)
   - Added `layout.padding.top: 30` to Chart.js options
   - Changed event marker `yAdjust` from -20 to 15 to position labels inside chart area
   - Increased timeline bar canvas height from 16px to 22px for label visibility

4. **[FIXED] Event markers appearing in wrong order**
   - Changed X-axis from category type (string labels) to linear type (numeric seconds)
   - Fixed annotation positioning to use numeric time values instead of string labels

5. **[FIXED] RoR Y-axis and spike filtering**
   - Made RoR Y-axis flexible with dynamic min/max based on data
   - Added filtering to only plot RoR values <= 30 to avoid chart spikes at beginning of roast

6. **[FIXED] UI improvements**
   - Changed "Temperature (°C)" to "Temp" on live roast page
   - Removed placeholder from event note input
   - Made panel heights align (stretch)
   - Moved dropdown menu to right side of header on roast detail page
   - Updated Power/Fan bar colors to muted earth tones
   - Made Basic Information section two columns on roast detail page
   - Made legend dots smaller (pointStyleWidth: 8, boxHeight: 8)
   - Reduced chart panel heights to 85% of original (370px)

7. **[FIXED] Dropdown menu not responding on roast detail page**
   - Fixed malformed Jinja2 template expressions (`{ {` -> `{{`) in reviewsData JavaScript object
   - The syntax error was preventing all JavaScript functions from being defined
