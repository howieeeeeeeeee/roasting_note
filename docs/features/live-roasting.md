# Live Roasting Interface

Real-time roasting control and monitoring at `/roast/live/<roast_id>`.

## Overview

The live roasting page provides a comprehensive interface for monitoring and controlling the roasting process in real-time.

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Setup Section (collapsible)                                │
│  [Bean Dropdown] [Weight Input] [Ambient Temp] [Humidity]   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                         TIMER                                │
│                        12:34                                 │
│                       (FC 08:45)                             │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────┐  ┌─────────────────────────────────────┐
│   Current Readings  │  │            Chart                    │
│   Temp: 185°C       │  │   [Temperature/RoR Graph]           │
│   RoR: 12.5°C/min   │  │   [Power Timeline Bar]              │
│                     │  │   [Fan Timeline Bar]                │
│   Fan:  [−] 9 [+]   │  └─────────────────────────────────────┤
│   Power:[−] 5 [+]   │  │            Data Tab                 │
│                     │  │   [Event Log Table]                 │
│   Quick Events:     │  │                                     │
│   [Y][FC][FC-E]     │  │                                     │
│   [SC][SC-E]        │  │                                     │
│                     │  │                                     │
│   [Add Event Form]  │  │                                     │
└─────────────────────┘  └─────────────────────────────────────┘
```

## Features

### Timer Display

- Large MM:SS format display
- Shows FC time in parentheses when First Crack logged
- Updates to latest FC if multiple FC events recorded

### Temperature Display

- Real-time temperature from K-Type sensor
- Updates every 1 second
- Shows "Offline" when sensor unavailable

### Rate of Rise (RoR)

- Calculated using 20-second sliding window
- Formula: `(current_temp - temp_20s_ago) × 3`
- Displays after 20 seconds of data collected
- Rounded to 1 decimal place

### Fan & Power Controls

- Range: 1-9 for both settings
- Default: Fan 9, Power 3
- Direct +/- stepper buttons
- Large touch-friendly display

### Quick Event Buttons

| Button | Event Name |
|--------|------------|
| Y | Yellowing |
| FC | First Crack Start |
| FC-end | First Crack End |
| SC | Second Crack Start |
| SC-end | Second Crack End |

### Add Event Form

- Temperature input (auto-filled from sensor if empty)
- Optional note field
- Logs to `temp_curve` array

## Data Logging

### Automatic Logging

- Temperature fetched every 1 second
- Logged to local CSV every second (`temp_logs/{roast_id}.csv`)
- Logged to database every 3 seconds with RoR value

### Manual Events

- Key timing events logged to `key_timings` array
- Include current temperature and settings

## Roast Lifecycle

1. **Pre-Start**: Setup section visible, timer at 00:00
2. **Start**: Click "Start Roast" → begins timer, starts polling
3. **During**: Log events, adjust settings, monitor chart
4. **End**: Click "End Roast" → stops timer, final temp logged
5. **Post**: Redirected to Edit page for roasted weight entry
