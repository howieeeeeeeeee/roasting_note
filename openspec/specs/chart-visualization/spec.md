
### Requirement: Dual-Axis Temperature and RoR Chart
The chart displays temperature (left axis) and RoR (right axis) over elapsed roast time.

#### Scenario: Temperature line
- **WHEN** a roast has `temp_curve` data
- **THEN** temperature is plotted as a blue line on the left Y-axis (scale: 0–200°C)

#### Scenario: RoR line
- **WHEN** RoR values are available
- **THEN** RoR is plotted as an orange line on the right Y-axis (fixed scale: -10 to 40°C/min)

#### Scenario: RoR spike filtering
- **WHEN** a RoR value exceeds 30°C/min
- **THEN** that data point is excluded from the chart to prevent visual distortion

---

### Requirement: Key Event Annotations
Vertical lines mark important timing milestones on the chart.

#### Scenario: Event annotation rendered
- **WHEN** a key timing event is logged (e.g., First Crack Start)
- **THEN** a vertical line annotation appears at the corresponding time on the chart
- **AND** the annotation is labeled with the event name

---

### Requirement: Fan and Power Overlay Bands
Fan and power settings are visualized as stepped bands on the chart.

#### Scenario: Power band
- **WHEN** power settings are present in `temp_curve`
- **THEN** a brown stepped band shows the power level over time

#### Scenario: Fan band
- **WHEN** fan settings are present in `temp_curve`
- **THEN** a green stepped band shows the fan level over time

#### Scenario: Band updates on settings change
- **WHEN** fan or power changes during a live roast
- **THEN** the stepped band updates to reflect the new value from that time forward

---

### Requirement: Dynamic X-Axis Range
The time axis adapts between live and historical view modes.

#### Scenario: Live roast extends automatically
- **WHEN** the roast is active and time exceeds 8 minutes
- **THEN** the X-axis extends automatically to always show all logged data

#### Scenario: Completed roast uses fixed range
- **WHEN** viewing a completed roast
- **THEN** the X-axis spans exactly the roast duration with no extra padding

---

### Requirement: Compact Chart Legend
The legend is readable without consuming excessive chart space.

#### Scenario: Legend displayed
- **WHEN** the chart is rendered
- **THEN** a compact point-style legend identifies the temperature and RoR lines and the power/fan bands
