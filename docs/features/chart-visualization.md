# Chart Visualization

Temperature and Rate of Rise (RoR) chart component used across the application.

## Shared Module

**File:** `static/js/roast-chart.js`

Used by:
- `roast_live.html` - Real-time updates during roasting
- `roast_detail.html` - Historical view of completed roasts
- `roast_edit.html` - View while editing roast data

## Chart Features

### Temperature Line (Left Y-Axis)
- Blue line showing temperature over time
- Scale: 0-200°C
- Point style: circle

### RoR Line (Right Y-Axis)
- Orange line showing rate of rise
- Scale: Fixed -10 to 40
- Supports negative values within fixed range
- Filtered: Only plots values <= 30 to avoid spikes

### X-Axis (Time)
- Linear scale using seconds
- Live mode: 8 minutes default, extends as needed
- Historical mode: Exact roast duration

### Event Markers
- Vertical annotations for key events (FC, SC, etc.)
- Labels positioned inside chart (yAdjust: 15)
- Events: Yellowing, First Crack, Second Crack

## Power/Fan Bands

Power and fan settings are shown as stepped, dashed bands inside the chart using a dedicated axis (`y-pf`).

### Visual Style
- Power: Brown shaded band
- Fan: Green shaded band
- Both use stepped lines with fill for band appearance

## API

### RoastChart.init(options)

Initialize the chart component.

```javascript
RoastChart.init({
  isLive: true,
  chartContainerId: 'roastCurveChart'
});
```

### RoastChart.initFromData(tempCurve, keyTimings, duration)

Load historical data (detail/edit pages).

```javascript
RoastChart.initFromData(tempCurve, keyTimings, roastDuration);
```

### RoastChart.addDataPoint(entry)

Add real-time data point (live page).

```javascript
RoastChart.addDataPoint({
  time_seconds: 180,
  temperature: 165,
  ror: 12.5,
  fan_setting: 9,
  power_setting: 5
});
```

### RoastChart.addEventMarker(name, timeSeconds)

Add event annotation.

```javascript
RoastChart.addEventMarker('First Crack Start', 542);
```

## Chart Configuration

### Layout Padding
```javascript
layout: {
  padding: { top: 30 }
}
```

### Legend
```javascript
legend: {
  position: 'top',
  labels: {
    usePointStyle: true,
    pointStyleWidth: 8,
    boxHeight: 8,
    font: { size: 11 }
  }
}
```

### CSS
```css
.chart-container-large {
  height: 370px;
}

```
