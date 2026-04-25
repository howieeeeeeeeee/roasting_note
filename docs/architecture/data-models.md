# Data Models

MongoDB collection schemas for RoastLogger.

## Collections

- [beans](#beans-collection) - Green coffee bean inventory
- [roasts](#roasts-collection) - Roasting sessions and profiles

---

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
  "note": "String"
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
```javascript
db.beans.updateOne(
  { _id: bean_id },
  { $inc: { stock_grams: -original_weight } }
)
```

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
