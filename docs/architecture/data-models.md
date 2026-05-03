# Data Models

MongoDB collection schemas for RoastLogger.

## Collections

- [beans](#beans-collection) - Green coffee bean inventory
- [roasts](#roasts-collection) - Roasting sessions and profiles

---

## Timestamp Policy

Application-created bean and roast documents include both `created_at` and
`updated_at`.

- Insert paths set both fields to the creation time.
- Update paths refresh `updated_at` on every mutated document.
- Form-update paths backfill `created_at` for legacy documents that are missing it.
- Database sync preserves source timestamps when possible and fills missing
  `created_at` / `updated_at` values on newly copied documents so future sync
  comparisons remain reliable.
- Application-created datetimes use the configured `TIMEZONE` for operator
  intent, but MongoDB persists BSON `Date` values as UTC instants. PyMongo reads
  those values back as naive UTC datetimes by default. Display formatting treats
  naive datetimes as UTC and converts them to `TIMEZONE`; duration and elapsed
  calculations continue to use the stored instants.

## `beans` Collection

Stores information about each type of green coffee bean in inventory.

```json
{
  "_id": "ObjectId",
  "name": "String",
  "origin": "String",
  "process": "String",
  "supplier": "String",
  "purchase_date": "Date",
  "purchase_price_total": "Decimal128",
  "purchase_weight_grams": "Integer",
  "unit_price_per_kg": "Decimal128",
  "stock_grams": "Integer",
  "short_flavor_notes": ["String"],
  "notes": "String",
  "color": "String",
  "archived": "Boolean",
  "created_at": "Date",
  "updated_at": "Date"
}
```

### Field Details

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | String | Yes | - | Bean name (e.g., "Ethiopia Yirgacheffe Gedeo") |
| `origin` | String | No | - | Country/region of origin |
| `process` | String | No | - | Processing method (Washed, Natural, Honey) |
| `supplier` | String | No | - | Where purchased |
| `purchase_date` | Date | No | - | When purchased |
| `purchase_price_total` | Decimal | No | - | Total cost for batch |
| `purchase_weight_grams` | Integer | No | - | Original batch weight |
| `stock_grams` | Integer | Yes | 0 | Current available stock |
| `short_flavor_notes` | Array[String] | No | [] | Compact flavor notes for bean previews and label auto-fill, one note per array item |
| `color` | String | No | "#6B8E6F" | Hex color for visual identification |
| `archived` | Boolean | No | false | Soft delete flag |
| `label` | Object | No | - | Label creator data (see below) |

### Embedded: `label` Object

Optional label configuration for the bean label creator.

```json
{
  "name": "String",
  "origin": "String",
  "process": "String",
  "roastLevel": "String",
  "flavorNotes": "String",
  "roastDate": "String",
  "templateId": "String",
  "fontPreset": "String",
  "aspectRatio": "String",
  "imageSrc": "String",
  "accentColor": "String",
  "exportWidthCm": "Number",
  "exportHeightCm": "Number",
  "customFields": {}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Display name on label (may differ from bean name) |
| `origin` | String | Origin text for label |
| `process` | String | Process method text for label |
| `roastLevel` | String | Roast level text (e.g., "Medium", "Light") |
| `flavorNotes` | String | Flavor notes text for label. May contain `\n`-separated lines; each non-blank line renders on its own line. |
| `roastDate` | String | Roast date (YYYY-MM-DD) |
| `templateId` | String | Selected template ID — one of `nova` / `ink` / `strip` / `washi` |
| `fontPreset` | String | Selected font preset — one of `modern` / `editorial` / `technical` / `bold` / `craft` |
| `aspectRatio` | String | Selected aspect ratio — one of `2:1` / `5:3` / `5:4` / `4:3` / `3:4` |
| `imageSrc` | String | Path to selected image (e.g. `/static/img/nova.png`) or empty for none |
| `accentColor` | String | Hex color for accent bar (typically bean color) |
| `exportWidthCm` | Number | Export width in cm |
| `exportHeightCm` | Number | Export height in cm |
| `customFields` | Object | Per-field overrides keyed by field name, each with optional `fontSize`, `fontFamily`, `color`, `x`, `y` |

---

## `roasts` Collection

Stores all data related to a single roasting session.

```json
{
  "_id": "ObjectId",
  "bean_id": "ObjectId",
  "title": "String",
  "roast_date": "Date",
  "original_weight_grams": "Integer",
  "roasted_weight_grams": "Integer",
  "weight_loss_percentage": "Float",
  "temp_measurement_method": "String",
  "roaster": "String",
  "ambient_temp_celsius": "Float",
  "ambient_humidity": "Integer",
  "lifecycle_status": "String",
  "roast_start_time": "Date",
  "roast_end_time": "Date",
  "roast_duration_seconds": "Integer",
  "key_timings": [],
  "temp_curve": [],
  "general_notes": "String",
  "reviews": [],
  "archived": "Boolean",
  "created_at": "Date",
  "updated_at": "Date"
}
```

`lifecycle_status` is written for new and updated roasts and uses:

| Value | Meaning |
| --- | --- |
| `draft` | Setup has been created but the live roast has not started. |
| `started` | The live roast timer has started and stock has been deducted when a bean/weight was provided. |
| `completed` | The roast is complete. This can come from the live **End Roast** action or the draft-only **Set to Completed** action. |

Older roasts without `lifecycle_status` remain readable by deriving lifecycle
from timestamps: `roast_end_time` means completed, `roast_start_time` without
`roast_end_time` means started, and neither timestamp means draft.

### Embedded: `key_timings` Array

Key events during roasting (Yellowing, First Crack, etc.)

```json
{
  "event_name": "String",
  "time_seconds": "Integer",
  "temperature": "Float",
  "fan_setting": "Integer",
  "power_setting": "Integer",
  "ror": "Float"
}
```

### Embedded: `temp_curve` Array

Temperature readings logged during roast.

```json
{
  "time_seconds": "Integer",
  "temperature": "Float",
  "fan_setting": "Integer",
  "power_setting": "Integer",
  "ror": "Float",
  "sensor_status": "String",
  "sensor_attempts": "Integer",
  "sensor_successes": "Integer",
  "sensor_read_ms": "Integer",
  "note": "String"
}
```

Automatic live-roast entries include sensor metadata. `sensor_status` is one of
`ok`, `retrying`, `stale`, `offline`, or `fault`.

### Embedded: `sensor_diagnostics` Array

Bounded anomaly log for live temperature reads. Only non-`ok` sync attempts are
persisted, and the array is sliced to the latest 300 entries.

```json
{
  "time_seconds": "Integer",
  "sensor_status": "String",
  "temperature": "Float | null",
  "attempts": "Integer",
  "successes": "Integer",
  "duration_ms": "Integer",
  "last_success_age_seconds": "Integer | null",
  "errors": ["String"],
  "diagnostics": {
    "status": "String",
    "error_code": "Integer",
    "errors": "Object"
  },
  "created_at": "Date"
}
```

### Embedded: `reviews` Array

Post-roast tasting reviews.

```json
{
  "_id": "ObjectId",
  "overall_score": "Integer",
  "extraction_method": "String",
  "notes": "String",
  "review_date": "Date",
  "created_at": "Date",
  "updated_at": "Date"
}
```

### Extraction Methods

- `espresso`
- `pourover`
- `ice_drop`
- `cold_brew`
- `other`

---

## Stock Management Logic

### On Roast Create

Draft roast creation writes `lifecycle_status: "draft"` and does not adjust
bean stock.

### On Roast Start

```javascript
db.beans.updateOne(
  { _id: bean_id },
  { $inc: { stock_grams: -original_weight } }
)
```

The roast also receives `roast_start_time` and `lifecycle_status: "started"`.

### On Roast End

Ending a started live roast writes `roast_end_time`,
`lifecycle_status: "completed"`, and appends the final live roast data such as
Drop timing when available.

### On Manual Draft Completion

Manually completing a draft writes `lifecycle_status: "completed"` and refreshes
`updated_at`. It does not create `roast_start_time`, `roast_end_time`,
temperature curve readings, sensor diagnostics, key timing events, a Drop event,
or bean-stock adjustments.

### On Roast Archive
```javascript
db.beans.updateOne(
  { _id: bean_id },
  { $inc: { stock_grams: +original_weight } }
)
db.roasts.updateOne(
  { _id: roast_id },
  { $set: { archived: true } }
)
```

### On Roast Weight Edit
Calculate difference and apply to bean stock.
