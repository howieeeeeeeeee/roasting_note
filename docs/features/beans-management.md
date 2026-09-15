# Bean Management

Create and maintain green-coffee bean records, current inventory, bean labels,
and the roast history associated with each bean.

> **Design specification:**
> [Bean inventory screens](../design/screens/bean-inventory.md)

## Access

- `/beans` lists active beans and links to add and detail views.
- `/beans/add` creates a bean.
- `/beans/detail/<bean_id>` shows bean data, stock history, and related roasts.
- `/beans/edit/<bean_id>` edits the current bean fields.

Archived beans are excluded from these active views. The Beans list hides
balances at or below zero by default; **Show Out of Stock** includes them.

## Purchase History

Each bean owns a `purchases` array. Add or edit purchases from bean detail or
its existing edit form without recreating the profile. A row records a date,
positive whole-gram weight, and optional total price; price per kg is derived.
A blank date or price means unknown. Removing an erroneous row subtracts its
weight from inventory when saved. A completely blank new row is ignored.

The latest purchase date is the maximum dated purchase. Summary weight is the
sum of all purchases. Lifetime cost and weighted average price per kg are
shown only when every purchase is priced; individual known prices remain
visible. Backdated entries do not replace a later latest-purchase date.

The canonical shapes are in [data models](../architecture/data-models.md#beans-collection).

## Stock Lifecycle

`stock = purchased grams - consumed roast grams + logged corrections + opening adjustment`

`stock_grams` remains the stored balance for fast list filtering and sorting.
Editing purchases changes that balance only by the purchased-weight difference.
Every form update atomically saves history, summaries, stock and `updated_at`.
A form version and a conditional document update reject stale submissions
with `409`; unsaved entries remain visible so the user can copy them before
reloading. Validation failures return `400` without partial changes.

- Creating a bean defaults stock to purchased weight. An optional opening
  count becomes its opening adjustment. Profile-only creation starts at zero.
- Starting a roast deducts its green weight once, including saved setup values.
- Archiving a started roast restores weight once; repeating archive does not.
- Editing a started roast applies its weight difference. Changing its bean
  transfers consumption, including when weight stays the same.
- Draft creation and manual draft completion do not change stock.
- **Correct stock to** records a signed `manual_correction` in the stock log.
  Leave it blank for automatic purchase accounting. Corrections apply after
  purchase changes in the same submission.
- **Set stock to zero** continues to record its signed correction.

Roast/bean updates retain the existing separate-document persistence model;
there is no distributed transaction or per-purchase allocation of roast usage.

## Beans List Remaining Meter

The Stock cell shows exact signed grams. Its separate meter uses
`clamp(stock_grams / cumulative purchased grams * 100, 0, 100)`.
Only the meter is clamped; raw stock still controls sorting and filtering.
Missing or invalid legacy purchase weights omit the meter. The Latest Purchase
and Avg. Price/kg columns use the summaries described above.

## Set Stock To Zero

Bean detail shows **More actions** only while `stock_grams` is a non-zero
integer. **Set stock to zero** works for positive and negative balances:

1. The confirmation names the bean, shows the signed current balance, and
   explains that the recorded change has no automatic undo.
2. Cancellation sends no request.
3. `POST /api/beans/<bean_id>/set-stock-zero` conditionally matches the
   observed balance, sets `stock_grams` to zero, appends one history entry, and
   refreshes `updated_at` with the same timestamp.
4. Success updates the stock badge and history in place, removes the action,
   and shows a toast. A failed or stale request leaves the page unchanged.

The signed `change_grams` value is `0 - previous_stock_grams`. Discarding a
positive balance therefore records a negative change; correcting a negative
balance records a positive change.

Repeated requests at zero cannot append another entry. A concurrent update to
a different balance returns a conflict so the user can refresh instead of
overwriting newer stock.

## Stock History

Bean detail renders `stock_change_log` newest-first under Stock & Pricing with
the recorded time, previous balance, signed change, and resulting balance.
Purchase additions and manual corrections do not erase earlier entries, so another later set-to-zero
event is appended to the same history.

## Local Migration

Preview before applying:

```bash
uv run python scripts/migrate_bean_purchases.py --dry-run
```

Pause local application writes, then run:

```bash
uv run python scripts/migrate_bean_purchases.py --apply
uv run python scripts/migrate_bean_purchases.py --dry-run
```

The command accepts only loopback `MONGO_URI_LOCAL`, uses a direct local
connection, and never constructs an online client. Apply backs up every local
collection with the existing canonical BSON backup/verification utilities
before changing beans. Backups and sanitized results stay in ignored
`db_backup/database_mirrors/local--<DEVICE>/...`.

Each legacy scalar purchase becomes one stable row. Current stock, bean ids,
labels, logs, roasts, and valid creation times are preserved. The opening
adjustment explains historical unlogged differences without inventing
purchases. Malformed records stop apply before backup/writes. Changed records
get fresh `updated_at`; existing arrays are skipped and reruns do not update
any timestamps. Conditional bean snapshots and a post-backup consumption check
reject intervening changes. Writes must remain paused until verification ends.

Legacy beans also render a projected purchase row before migration; saving an
unmigrated valid bean initializes its array and opening adjustment in the same
conditional write. Unsupported legacy values need local correction first.

## Database Selection And Sync

Bean edits write only the selected database. A guarded timestamp-aware sync
copies the complete newer bean, including purchases, corrections, and summary
fields. It does not merge purchase rows across devices. Deploy compatible code
before syncing migrated beans online; review a fresh local-to-online dry run
and any conflicts first. Remote-only roasts are not a local reconciliation
source. An applied mirror remains a separate authorized operation.

See [Guarded Database Sync](./database-sync.md) for the operator flow.
