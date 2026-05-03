---
id: RN-0019
title: Show Roast Times in Operator Timezone (Not Raw UTC Clock)
type: bug
status: resolved
priority: medium
created: 2026-05-02
resolved: 2026-05-03
area: live-roasting
tags:
  - timezone
  - ux
---

# Show Roast Times in Operator Timezone (Not Raw UTC Clock)

## Description

Operators in US Eastern Time see roast timestamps on the roasts index and roast detail screens that read like “2026-05-03 00:40” after an evening roast on May 2, which feels like incorrect data collection even when the underlying instants match reality.

## Details

### Diagnosis (2026-05-02, local `roastlogger` DB sample)

Recent completed roasts (e.g. Kenya, Bishan, Watermelon, Passionfruit, Gucci Washed Dark) have `roast_start_time` values such as:

- `2026-05-02 23:57:30` (Kenya — first roast of the evening)
- `2026-05-03 00:09–00:41` for subsequent roasts on the same session

Against these rows in MongoDB, values are **`datetime` with `tzinfo None`** (PyMongo default for BSON `Date` — stored as milliseconds since Unix epoch in **UTC**).

Interpreting those naïve datetimes as **UTC** and converting to **`America/New_York` (EDT, UTC−4)** yields wall times on **May 2 between ~7:57 PM and ~8:41 PM**, which matches “May 2 ~8 PM East Coast roast night.” So **collection/storage of the instant is consistent with correct behaviour**; the bug is primarily **presentation**.

### Root cause

- `POST /api/roast/start/` sets `roast_start_time` via `get_current_time_with_tz()` (`datetime.now(local_tz)` with `TIMEZONE` default `America/New_York`). PyMongo persists that instant in BSON as UTC.
- On read, datetimes typically come back as **naïve UTC**.
- `@app.template_filter("format_date")` documents itself as *“no timezone conversion - shows DB value as-is”* and formats with `%Y-%m-%d %H:%M`. That prints the **UTC clock face**, not the operator-local wall time.

Same filter is used for `roast_date`, `roast_end_time`, reviews, etc., so anywhere it is used without conversion may feel “off” relative to Eastern (or whichever `TIMEZONE` the server is configured for).

### Out of scope (unless product decides otherwise)

- Changing how durations or `elapsed_seconds` are computed (those are deltas; unaffected if start/end share the same representation).
- Forcing browsers to infer tz from JS without a server-side convention — prefer aligning display with **`TIMEZONE` env / operator expectation** documented in deployment.

### Optional data repair

**Do not blindly subtract hours in Mongo.** For the sampled May 2026 session above, timestamps are correct instants; “fixing” them would corrupt data.

If historical audit finds documents that were mistakenly written as *local-clock naïve* treated as UTC, remediation would need a **per-document heuristic** — out of scope here unless surfaced by a dedicated audit ticket.

### Verification snippet (read-only — run against a backup or local DB)

Use this to confirm a naïve `roast_start_time` matches Eastern wall time:

```python
"""Read-only check: naive Mongo datetimes ↔ Eastern wall clock."""

from pymongo import MongoClient
from datetime import datetime, timezone

import pytz

EASTERN = pytz.timezone("America/New_York")
uri = "mongodb://localhost:27017/"
col = MongoClient(uri).roastlogger.roasts

for r in col.find(
    {"title": {"$in": ["Kenya", "Gucci Washed Dark"]}},
    {"title": 1, "roast_start_time": 1},
):
    naive = r.get("roast_start_time")
    if naive is None:
        continue
    # BSON instant is UTC; naive from PyMongo → interpret as UTC
    utc_dt = naive.replace(tzinfo=timezone.utc)
    eastern = utc_dt.astimezone(EASTERN)
    print(r["title"], "stored naive:", naive, "| Eastern:", eastern.strftime("%Y-%m-%d %H:%M %Z"))
```

Expected pattern for correct data: Eastern date stays on May 2 for an ~8 PM session.

### If migration is ever warranted (only after audit — not recommended for reported case)

A future implementer could use the same UTC→`TIMEZONE.astimezone` rule to detect outliers; **any** `$set` of `roast_start_time` / `roast_end_time` should preserve the intended instant (epoch milliseconds), never “shift the clock” without proving the stored epoch is wrong.

## Acceptance Criteria

- [x] Roast list “Date” column shows **wall time in the configured operator timezone** (same semantics as `TIMEZONE` / product decision), not raw UTC digits, OR the UI explicitly labels “UTC” if product chooses UTC display.
- [x] Roast detail start/end times (and related date fields using the same filter) behave consistently with the chosen rule.
- [x] Naïve datetimes loaded from Mongo are interpreted consistently (**document** whether they are treated as UTC, matching PyMongo BSON contract).
- [x] No regression on duration/elapsed computations.
- [x] Relevant docs updated when implemented: `docs/features/live-roasting.md`, `docs/architecture/data-models.md` (timestamp / display note under Timestamp Policy), and any affected `docs/design/` screen doc for the roast list / detail screens.

## Open Questions

- Should the app always use **`TIMEZONE` env** for display, or should per-user timezone (browser or profile) be supported later? (Default MVP: honour `TIMEZONE` consistently.)

## Related Files

- `app.py`
- `templates/index.html`
- `templates/roast_detail.html`
- `templates/beans_detail.html`
- `.env.example` (document `TIMEZONE` for deployed vs local parity)
