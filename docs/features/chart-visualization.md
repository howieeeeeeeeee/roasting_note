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
- Scale: Dynamic based on data (rounds to nearest 10)
- Supports negative values
- Filtered: Only plots values <= 30 to avoid spikes

### X-Axis (Time)
- Linear scale using seconds
- Live mode: 8 minutes default, extends as needed
- Historical mode: Exact roast duration

### Event Markers
- Vertical annotations for key events (FC, SC, etc.)
- Labels positioned inside chart (yAdjust: 15)
- Events: Yellowing, First Crack, Second Crack

## Power/Fan Timeline Bars

Below the main chart, segmented bars show power and fan settings.

### Segment Detection
- Scans data to detect when settings change
- Creates distinct segments for each setting period

### Visual Style
- Power: Brown/red gradient (1=light, 9=dark)
- Fan: Green gradient (1=light, 9=dark)
- Labels (P4, F9) shown on segments > 20px wide
- Borders between segments

### Color Palettes

**Power (Earth Tones):**
```javascript
{
  1: '#F5F0EB', 2: '#E8DDD4', 3: '#D4C4B5',
  4: '#C0AB96', 5: '#A89282', 6: '#8F7A6A',
  7: '#7A6658', 8: '#6B5B4D', 9: '#5A4D42'
}
```

**Fan (Greens):**
```javascript
{
  1: '#EDF3EE', 2: '#DAE7DC', 3: '#C4D9C7',
  4: '#ADCAB2', 5: '#96BA9C', 6: '#7FAA87',
  7: '#6B9A74', 8: '#6B8E6F', 9: '#5A7A5E'
}
```

## API

### RoastChart.init(options)

Initialize the chart component.

```javascript
RoastChart.init({
  isLive: true,
  chartContainerId: 'roastCurveChart',
  powerCanvasId: 'powerTimeline',
  fanCanvasId: 'fanTimeline'
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

.pf-timeline-canvas {
  height: 22px;
}
```
