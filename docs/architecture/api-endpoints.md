# API Endpoints

All REST API routes for RoastLogger.

## HTML-Rendering Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard (list of roasts) |
| `/beans` | GET | List of beans |
| `/beans/add` | GET | Add bean form |
| `/beans/edit/<bean_id>` | GET | Edit bean form |
| `/beans/detail/<bean_id>` | GET | Bean detail page |
| `/roast/new` | GET | Create draft roast and redirect to live |
| `/roast/live/<roast_id>` | GET | Live roasting page |
| `/roast/detail/<roast_id>` | GET | Roast detail page |
| `/roast/edit/<roast_id>` | GET | Edit roast form |

---

## Bean API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/beans/add` | POST | Create new bean |
| `/api/beans/edit/<bean_id>` | POST | Update bean |
| `/api/beans/delete/<bean_id>` | POST | Archive bean (soft delete) |
| `/api/beans/<bean_id>/label` | POST | Save label creator data for a bean |

---

## Roast API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/roast/create` | POST | Create draft roast, returns `{ new_roast_id }` |
| `/api/roast/update/<roast_id>` | POST | Update roast data |
| `/api/roast/delete/<roast_id>` | POST | Archive roast (soft delete, restore stock) |
| `/api/roast/start/<roast_id>` | POST | Set `roast_start_time` |
| `/api/roast/end/<roast_id>` | POST | Set `roast_end_time` |
| `/api/roast/update_title/<roast_id>` | POST | Update roast title |
| `/api/roast/add_timing/<roast_id>` | POST | Add key timing event |
| `/api/roast/add_event/<roast_id>` | POST | Add temp curve event |
| `/api/roast/log_temp_local/<roast_id>` | POST | Log to local CSV file |
| `/api/roast/sync_state/<roast_id>` | POST | Sync live roast state (temp, RoR, settings) to DB |

---

## Review API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/roast/add_review/<roast_id>` | POST | Add review to roast |
| `/api/roast/update_review/<roast_id>/<review_id>` | POST | Update review |
| `/api/roast/delete_review/<roast_id>/<review_id>` | POST | Delete review |

---

## Temperature API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/temp/current_fast` | GET | Fast single-request temperature fetch for UI polling (200ms timeout) |
| `/api/temp/current` | GET | Accurate temperature fetch — 3 requests, averages top 2 (100ms timeout each) |

### Response Format

**Success:**
```json
{
  "temperature": 190,
  "status": "success"
}
```

**Error:**
```json
{
  "temperature": null,
  "status": "error",
  "message": "Service unavailable or timeout"
}
```

---

## Settings & Sync API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/settings/db` | GET | Get current database mode |
| `/api/settings/db` | POST | Switch database mode |
| `/api/settings/sensor` | GET | Get current sensor URL |
| `/api/settings/sensor` | POST | Set sensor URL |
| `/api/sync/online-to-local` | POST | Sync online DB to local |
| `/api/sync/local-to-online` | POST | Sync local DB to online |
| `/api/db/clean-test-data` | POST | Delete test data (`test_data: True`) from local DB |
| `/api/db/clean-local` | POST | Delete ALL data from local DB |

### Database Mode Response

```json
{
  "mode": "local"
}
```

### Sync Response

```json
{
  "success": true,
  "beans": { "added": 5, "updated": 2 },
  "roasts": { "added": 10, "updated": 3 }
}
```

### Clean Test Data Response

```json
{
  "success": true,
  "beans_deleted": 3,
  "roasts_deleted": 5,
  "temp_logs_deleted": 2
}
```

---

## Request/Response Examples

### Add Key Timing Event

**POST** `/api/roast/add_timing/<roast_id>`

```json
{
  "event_name": "First Crack Start",
  "time_seconds": 542,
  "temperature": 190,
  "fan_setting": 9,
  "power_setting": 4
}
```

### Add Temperature Event

**POST** `/api/roast/add_event/<roast_id>`

```json
{
  "time_seconds": 180,
  "temperature": 165,
  "fan_setting": 9,
  "power_setting": 5,
  "ror": 12.5,
  "note": "Increased power"
}
```

### Save Bean Label

**POST** `/api/beans/<bean_id>/label`

```json
{
  "name": "Ethiopia Yirgacheffe",
  "origin": "Ethiopia",
  "process": "Washed",
  "roastLevel": "Medium",
  "flavorNotes": "Berry, Citrus",
  "roastDate": "2025-02-23",
  "templateId": "minimal",
  "imageSrc": "/static/img/nova.png",
  "accentColor": "#6B8E6F",
  "exportWidthCm": 5,
  "exportHeightCm": 4
}
```

**Response:** `{ "success": true }` or `404` if bean not found.

### Add Review

**POST** `/api/roast/add_review/<roast_id>`

```json
{
  "overall_score": 4,
  "extraction_method": "espresso",
  "notes": "Bright acidity, fruity notes"
}
```
