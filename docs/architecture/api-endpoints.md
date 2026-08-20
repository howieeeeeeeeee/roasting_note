# API Endpoints

All REST API routes for RoastLogger.

## HTML-Rendering Routes

| Route | Method | Description |
| --- | --- | --- |
| `/` | GET | Dashboard (list of roasts) |
| `/beans` | GET | List of beans |
| `/beans/add` | GET | Add bean form |
| `/beans/edit/<bean_id>` | GET | Edit bean form |
| `/beans/detail/<bean_id>` | GET | Bean detail page |
| `/roast/new` | GET | Create draft roast and redirect to live |
| `/roast/live/<roast_id>` | GET | Live roasting page |
| `/roast/detail/<roast_id>` | GET | Roast detail page |
| `/roast/edit/<roast_id>` | GET | Edit roast form |

Invalid BSON ObjectId path values return HTTP `400`. API paths return
`{"success": false, "error": "Invalid identifier"}`; rendered-page paths
return the same message as plain text.

---

## Bean API Routes

| Route | Method | Description |
| --- | --- | --- |
| `/api/beans/add` | POST | Create new bean |
| `/api/beans/edit/<bean_id>` | POST | Update bean |
| `/api/beans/delete/<bean_id>` | POST | Archive bean (soft delete) |
| `/api/beans/<bean_id>/set-stock-zero` | POST | Conditionally set non-zero stock to zero and append bean stock history |
| `/api/beans/<bean_id>/label` | POST | Save label creator data for a bean |
| `/api/label/preferences` | GET | Default `templateId` / `fontPreset` / `aspectRatio` for new beans, derived from the most recent saved label |
| `/api/label/images` | GET | List image assets under `/static/img/` for the label image picker |

### Set Bean Stock To Zero

`POST /api/beans/<bean_id>/set-stock-zero` accepts no body. Success returns:

```json
{
  "success": true,
  "previous_stock_grams": -25,
  "change_grams": 25,
  "stock_grams": 0,
  "stock_change": {
    "event_type": "set_to_zero",
    "previous_stock_grams": -25,
    "change_grams": 25,
    "resulting_stock_grams": 0,
    "recorded_at": "2026-08-20T11:15:00-04:00"
  }
}
```

The endpoint returns `404` / `Bean not found` for missing or archived beans,
`409` / `Bean stock is already zero` at zero, and `409` / `Bean stock changed;
refresh and try again` when the observed balance loses a concurrent update.
Malformed ObjectIds use the shared `400` / `Invalid identifier` response.

---

## Roast API Routes

| Route | Method | Description |
| --- | --- | --- |
| `/api/roast/create` | POST | Create draft roast, returns `{ new_roast_id }` |
| `/api/roast/update/<roast_id>` | POST | Update roast data |
| `/api/roast/delete/<roast_id>` | POST | Archive roast (soft delete, restore stock) |
| `/api/roast/start/<roast_id>` | POST | Set `roast_start_time` and `lifecycle_status: "started"` |
| `/api/roast/end/<roast_id>` | POST | Set `roast_end_time` and `lifecycle_status: "completed"` |
| `/api/roast/update_setup/<roast_id>` | POST | Save draft setup fields before roast start |
| `/api/roast/complete_draft/<roast_id>` | POST | Mark a draft roast completed without creating live-roast data |
| `/api/roast/update_title/<roast_id>` | POST | Update roast title |
| `/api/roast/add_timing/<roast_id>` | POST | Add key timing event |
| `/api/roast/add_event/<roast_id>` | POST | Add temp curve event |
| `/api/roast/log_temp_local/<roast_id>` | POST | Log to local CSV file |
| `/api/roast/sync_state/<roast_id>` | POST | Sync live roast state (temp, RoR, settings) to DB |

`/api/roast/sync_state/<roast_id>` returns the temperature fields documented
below plus `ror`, `logged_to_db`, and `last_success_age_seconds` so the live UI
can distinguish fresh, retrying, stale, offline, and faulted sensor states.

---

## Review API Routes

| Route | Method | Description |
| --- | --- | --- |
| `/api/roast/add_review/<roast_id>` | POST | Add review to roast |
| `/api/roast/update_review/<roast_id>/<review_id>` | POST | Update review |
| `/api/roast/delete_review/<roast_id>/<review_id>` | POST | Delete review |

---

## Temperature API Routes

| Route | Method | Description |
| --- | --- | --- |
| `/api/temp/current_fast` | GET | Single-attempt temperature fetch for lightweight checks |
| `/api/temp/current` | GET | Accurate temperature fetch — 3 attempts, averages top 2 when available |
| `/api/temp/test_connection` | GET | Retrying sensor connection test with diagnostics for the settings modal |

### Response Format

**Success:**

```json
{
  "temperature": 190,
  "status": "success",
  "sensor_status": "ok",
  "attempts": 3,
  "successes": 3,
  "duration_ms": 640
}
```

**Error:**

```json
{
  "temperature": null,
  "status": "error",
  "sensor_status": "offline",
  "attempts": 3,
  "successes": 0,
  "duration_ms": 2250,
  "message": "timeout"
}
```

`sensor_status` may be `ok`, `retrying`, `stale`, `offline`, or `fault`.
`/api/temp/test_connection` includes `diagnostics` when the ESP32
`/diagnostics` endpoint can explain a hardware fault.

---

## Settings & Sync API Routes

| Route | Method | Description |
| --- | --- | --- |
| `/api/settings/db` | GET | Get current database mode |
| `/api/settings/db` | POST | Switch database mode |
| `/api/settings/sensor` | GET | Get current sensor URL |
| `/api/settings/sensor` | POST | Set sensor URL |
| `/api/sync/preflight/<direction>` | POST | Audited, read-only sync preflight for a supported direction |
| `/api/sync/runs/active` | GET | Restore the sanitized active browser run, if any |
| `/api/sync/runs/<run-id>/backup` | POST | Accept the exact first token and create/verify the complete backup |
| `/api/sync/runs/<run-id>/apply` | POST | Accept the exact second token and run timestamp-aware sync |
| `/api/sync/runs/<run-id>/cancel` | POST | Cancel an awaiting-apply run while retaining its backup |
| `/api/sync/online-to-local` | POST | Fail-closed legacy route; returns CLI migration guidance |
| `/api/sync/local-to-online` | POST | Fail-closed legacy route; returns CLI migration guidance |
| `/api/db/clean-test-data` | POST | Delete test data (`test_data: True`) from local DB |
| `/api/db/clean-local` | POST | Delete ALL data from local DB |

### Database Mode Response

```json
{
  "mode": "local",
  "default": "local"
}
```

Dedicated E2E mode adds `e2e_mode: true`, `local_database:
"roastlogger_e2e"`, and `test_run_id`. It forces `mode: "local"`; attempts to
select online mode return HTTP `409`. Both global cleanup routes also return
HTTP `409` in E2E mode and direct the operator to run-scoped harness cleanup.

Ordinary E2E sync preflight is audited into ignored run artifacts but returns
HTTP `503` without endpoint access; its phase routes return `409`. The explicit
browser sync simulation injects an artifact-only executor and may use the phase
routes without constructing an online client. Historic sync POST routes always
return HTTP `409`.

### Sync Preflight Response

```json
{
  "success": true,
  "run_id": "20260729T130000Z-1234abcd",
  "audit_recorded": true,
  "audit_path": "docs/audit_history/database_mirrors/2026/07/...",
  "apply_eligible": true,
  "backup_confirmation": "BACKUP 20260729T130000Z-1234abcd",
  "plan": {
    "direction": "online-to-local",
    "source": {"role": "online", "host": "cluster.example", "database": "roastlogger"},
    "destination": {"role": "local", "host": "localhost:27017", "database": "roastlogger"},
    "source_counts": {"beans": 5, "roasts": 10},
    "destination_counts": {"beans": 4, "roasts": 9},
    "backup": {"scope": "complete_destination_database"},
    "cli_command": "uv run python scripts/sync_database.py --direction online-to-local"
  }
}
```

This route reads connectivity, collection metadata, and counts; it never writes
to either database or creates a backup. It writes one terminal UI-intent audit
record for every request, including failed preflights. `apply_eligible` is true
only when the direct request peer and request host are loopback and the runtime
is not ordinary E2E. A hosted/non-loopback success omits
`backup_confirmation`. An audit persistence failure returns HTTP `500` with
`audit_recorded: false`; a safely recorded preflight failure returns HTTP
`503`.

### Browser Sync Phase Boundary

All four run endpoints require both the direct peer address and `Host` to be
loopback. `X-Forwarded-For`, `Forwarded`, and similar headers never establish
locality. Mutation requests additionally require `application/json`; when an
`Origin` header is supplied, its scheme, host, and effective port must equal
the request origin. Access failures happen before database, backup, state, or
audit activity.

The backup request is:

```json
{
  "direction": "online-to-local",
  "confirmation": "BACKUP 20260729T130000Z-1234abcd"
}
```

It succeeds only for a server-held, process-local preview capability. The first
backup attempt atomically consumes that capability. A wrong first token returns
`400`; a competing request, process restart, or worker loss requires a fresh
preview. Exact confirmation atomically claims the sole active-run slot before
backup. Another preview may still return a read-only plan, but its later
backup request receives `409` without changing the winning claim.

Successful backup returns `stage: awaiting_apply`, a sanitized backup summary,
and the exact `apply_confirmation`. `GET /api/sync/runs/active` returns the same
state with `restored: true` after it has reconstructed runtime identity and
reverified the manifest and every payload. With no run it returns
`{"success": true, "active": null}`. It never returns URIs, credentials, raw
documents, or submitted confirmation text.

The apply request is:

```json
{
  "direction": "online-to-local",
  "confirmation": "APPLY online-to-local 20260729T130000Z-1234abcd"
}
```

The cancel request contains only `direction`. Both require the matching active
run in `awaiting_apply`; invalid stages, direction mismatches, replay, or a
different run return `409`. Apply and cancel atomically compete for one
terminal-transition marker, so concurrent terminal requests cannot both run or
write audits. A wrong apply token returns `400` and leaves the verified run
available for exact retry or cancellation. Terminal responses include status,
backup summary, collection/aggregate sync results when available, and a
repository-relative audit or recovery path.

Atomic run state and the cross-process exclusive claim live under ignored
`db_backup/database_mirrors/`. An interrupted phase or corrupt/inconsistent
state remains claimed and returns `stage: recovery_required`; the API never
silently discards, overwrites, or repeats it.

The two historic sync routes return HTTP `409`, perform no database or
filesystem operation, and direct the caller to guarded local Settings or the
CLI documented in [Database Sync](../features/database-sync.md).

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
  "flavorNotes": "Berry\nCitrus",
  "roastDate": "2025-02-23",
  "templateId": "nova",
  "fontPreset": "modern",
  "aspectRatio": "5:4",
  "imageSrc": "/static/img/nova.png",
  "accentColor": "#6B8E6F",
  "exportWidthCm": 5,
  "exportHeightCm": 4
}
```

`flavorNotes` may contain `\n`-separated lines; each non-blank line is rendered on its own line on the label.

**Response:** `{ "success": true }` or `404` if bean not found.

### Get Label Defaults

**GET** `/api/label/preferences`

Returns the template / font / aspect-ratio triplet to use when seeding the label modal for a bean that has no saved label of its own. The values come from the most recently updated non-archived bean that has a saved `label.templateId`. If no bean has a saved label yet, returns the hardcoded fallback.

**Response:**

```json
{
  "templateId": "ink",
  "fontPreset": "editorial",
  "aspectRatio": "5:4"
}
```

`templateId` is one of `nova` / `ink` / `strip` / `washi`. `fontPreset` is one of `modern` / `editorial` / `technical` / `bold` / `craft`. `aspectRatio` is one of `2:1` / `5:3` / `5:4` / `4:3` / `3:4`.

### Add Review

**POST** `/api/roast/add_review/<roast_id>`

```json
{
  "overall_score": 4,
  "extraction_method": "espresso",
  "notes": "Bright acidity, fruity notes"
}
```
