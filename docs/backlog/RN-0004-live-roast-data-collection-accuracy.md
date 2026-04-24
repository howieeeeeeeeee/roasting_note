---
id: RN-0004
title: Live Roast Data Collection Accuracy
type: improvement
status: resolved
priority: high
created: 2026-01-11
resolved: 2026-01-11
area: live-roasting
branch: feat/data-collection-improvements
tags:
  - ror
  - database-logging
---

# Live Roast Data Collection Accuracy

## Resolution Summary

Implemented both solutions:

1. **RoR Calculation Fixed** (`app.py:812-851`)
   - Added configurable constants: `ROR_WINDOW_SECONDS = 20`, `ROR_TOLERANCE_SECONDS = 5`
   - Now uses 20-second window (matching documentation)
   - Finds *closest* reading within tolerance window (eliminates gaps)

2. **Database Logging Increased** (`app.py:48`)
   - Added `DB_LOG_INTERVAL_SECONDS = 1`
   - Now logs every 1 second (consistent with CSV)

All 58 tests pass.

---

## Original Problems

### 1. RoR Data Has Gaps During Roast

**What's happening:**

- RoR values are sometimes missing in the middle of roasts (not just at the start)
- Code uses 30-second window but documentation says 20 seconds (mismatch)
- RoR calculation looks for reading at exactly `target_time ± 2s` - too strict
- If no reading found in that narrow window, RoR returns `None` (gap)

**Current Code (`app.py` lines 805-846):**
```python
# Uses 30s window (should be 20s per docs)
target_time = current_time - 30

# Only accepts reading within ±2 seconds of target - too strict
if reading['time'] <= target_time + 2:
    past_reading = reading
```

**Why this matters:**

- Missing RoR data makes it hard to analyze what happened during the roast
- Want to record accurate RoR values throughout the entire roast
- Need reliable data for comparing and replicating roast profiles

**Reference:** `docs/features/live-roasting.md` (lines 53-54) - Formula should use 20-second window

### 2. Database Logging Interval May Be Too Coarse

**What's happening:**

- Temperature fetched every 1 second
- CSV logs every 1 second  
- Database logs only every 5 seconds
- Mismatch between CSV and database data

**Questions:**

- Can we save to database every second as well? (and maybe we can drop the need for local csv)
- Will the system handle the increased load without lag?
- Can the frontend plot more data points efficiently?
- Is there a performance impact we need to test?

**Reference:** `docs/features/live-roasting.md` (lines 83-87)

---

## Proposed Solutions

### Solution 1: Fix RoR Calculation

**Changes Required:**

1. **Add configurable constants at top of `app.py`:**
   ```python
   # RoR Calculation Settings
   ROR_WINDOW_SECONDS = 20      # How far back to look for comparison temp
   ROR_TOLERANCE_SECONDS = 2    # Acceptable deviation from target time
   ```

2. **Fix window mismatch:** Change from 30s to use `ROR_WINDOW_SECONDS` constant

3. **Improve reading search:** Instead of requiring exact match within tolerance, find the *closest* reading within tolerance window, or use interpolation

4. **Verify real time gap is used:** The code already correctly uses `(temp_diff / time_diff) * 60` ✓

**Files to Modify:**
- `app.py` - Add constants and update `calculate_ror()` function

---

### Solution 2: Increase Database Logging Frequency

**Current State:**
- MongoDB logs every 5 seconds (`client_time // 5`)
- Local CSV logs every 1 second
- Creates data mismatch

**Proposed Options:**

| Option | Interval | Pros | Cons |
|--------|----------|------|------|
| A. Log every 1s | 1 second | Consistent with CSV, could drop CSV | Higher DB load |
| B. Log every 2s | 2 seconds | Good balance | Still some mismatch |
| C. Batch logging | 5s batch of 5 readings | Same DB calls, complete data | Delayed persistence |

**Recommended:** Option A (1s logging) - test performance first

**Files to Modify:**
- `app.py` - `api_roast_sync_state()` function - change interval logic (line 883)

---

## Success Criteria

- ✅ RoR window and tolerance are configurable constants (`ROR_WINDOW_SECONDS`, `ROR_TOLERANCE_SECONDS`)
- ✅ RoR uses 20-second window (matching documentation)
- ✅ RoR calculation finds closest reading within tolerance (no gaps)
- ✅ RoR uses actual time difference for calculation (already correct: `(temp_diff / time_diff) * 60`)
- ✅ Evaluate 1-second database logging - if performance allows, implement it
- ✅ Frontend chart handles increased data without lag
- ✅ CSV and database data are consistent

---

## Implementation Phases

### Phase 1: RoR Calculation Improvements
1. Add configurable constants at top of `app.py`:
   - `ROR_WINDOW_SECONDS = 20`
   - `ROR_TOLERANCE_SECONDS = 2`
2. Update `calculate_ror()` to use these constants instead of hardcoded values
3. Improve reading search to find closest reading within tolerance window
4. Optionally add interpolation for more accurate RoR

### Phase 2: Database Logging Frequency
1. Test 1-second DB logging performance
2. If acceptable, update interval in `api_roast_sync_state()` (change `client_time // 5` to `client_time // 1`)
3. Consider deprecating local CSV logging if DB has all data

---

## Related Documentation

- `docs/features/live-roasting.md` - Current data logging behavior
- `docs/features/temperature-sensor.md` - Temperature sensor details
