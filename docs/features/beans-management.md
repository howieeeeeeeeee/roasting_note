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

## Bean Data

Bean records include profile, sourcing, purchase, stock, notes, display color,
optional label data, and timestamps. The canonical document shape is in
[data models](../architecture/data-models.md#beans-collection).

New beans initialize `stock_change_log` to an empty array. Existing beans that
do not have the field remain valid and render an empty history.

## Stock Lifecycle

- Editing a bean writes the submitted current stock directly.
- Starting a roast deducts its original green weight once.
- Archiving a started roast restores its original green weight.
- Editing the weight of a started roast applies the difference.
- Draft creation and manual draft completion do not change stock.

Those existing operations do not add `stock_change_log` entries. The log is
currently reserved for the explicit set-to-zero action.

## Beans List Remaining Meter

Each Beans-list Stock cell keeps the exact signed balance in a compact
`<stock_grams>g left` pill. When `purchase_weight_grams` is a positive integer,
a separate thin meter beneath the pill shows the remaining share of the
original purchase:

`clamp((stock_grams / purchase_weight_grams) * 100, 0, 100)`

The clamp affects only the meter. Zero and negative balances produce an empty
meter, balances above the original purchase produce a full meter, and the pill
continues to show the uncapped value. A missing, non-integer, zero, or negative
purchase weight omits the meter and leaves the signed pill as the complete
fallback. Sorting and out-of-stock filtering continue to use raw
`stock_grams`; the indicator does not store or change inventory data.

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
Manual restocking does not erase earlier entries, so another later set-to-zero
event is appended to the same history.

## Database Selection And Sync

The action writes only the currently selected `beans` collection. It does not
contact the other database role or modify `roasts`. A later guarded
timestamp-aware sync copies the complete bean, including its embedded history,
when that bean is the newer source document. No migration, backfill, or applied
mirror is part of this feature.

See [Guarded Database Sync](./database-sync.md) for dry-run, authorization,
backup, and audit requirements.
