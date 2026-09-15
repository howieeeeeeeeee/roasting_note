---
id: RN-0031
title: Repeat bean purchases with preserved inventory and local migration
type: feature
status: resolved
priority: high
created: 2026-09-15
resolved: 2026-09-15
area: beans
parent:
decisions: []
blocked_by: []
testing_policy: v1
tags: [beans, inventory, purchases, migration, database-sync]
---

# Repeat bean purchases with preserved inventory and local migration

## Description

Record repeated purchases on the existing bean so its profile, labels, and
roast history stay together. Show purchase history, the latest purchase date,
and stock that accounts for purchased weight, roast consumption, and explicit
inventory corrections; migrate existing local beans without changing balances.

## Details

### Current behavior and evidence

- `models/bean_helpers.py` stores one `purchase_date`,
  `purchase_weight_grams`, and `purchase_price_total`; it calculates
  `unit_price_per_kg`. The form accepts total price, not unit price.
- The edit form directly overwrites both purchase fields and current stock.
  Starting a roast deducts weight, archiving a started roast restores weight,
  and editing a started roast adjusts consumption. Draft creation and manual
  draft completion do not consume inventory.
- RN-0025 logs explicit set-to-zero corrections in `stock_change_log`, but
  historical manual stock edits were not logged. RN-0027's remaining meter
  uses the single purchase weight as its denominator.
- Read-only local inspection on 2026-09-15 found 13 non-test beans, all active,
  all with a purchase date, positive integer purchase weight, and Decimal128
  total price; none already has `purchases`. Three have zero-stock history.
  Three balances differ from purchase weight minus active started-roast usage
  plus recorded corrections. A naive historical recalculation would change
  those balances and must not be the migration strategy.

### Minimum implementation

Use one embedded `purchases` array on each bean, the existing forms and MongoDB
collection, and the existing guarded document sync. Do not add an inventory
collection, inventory service framework, or dependency.

Each purchase contains a stable `id`, `purchase_date`, positive integer
`weight_grams`, and optional nonnegative Decimal128 `price_total`. Derive the
entry's price per kg with Decimal arithmetic. A legacy missing date or price
remains unknown rather than becoming today's date or zero cost.

- Add a repeatable purchase section to the existing bean form: add a row,
  correct a row, or remove an incorrectly entered row. Preserve stable row ids;
  reject malformed dates, invalid/duplicate ids, non-finite or negative prices,
  and zero, negative, boolean, or fractional weights without partial writes.
- Creating a bean records its initial purchase. Existing beans can receive a
  new purchase without re-entering their profile, supplier, notes, or labels.
  Retain the minimal profile-only creation path with empty history and zero
  stock when no purchase is supplied.
- Bean detail shows history newest purchase date first with date, grams,
  total price, and derived price per kg. Latest purchase date is the maximum
  recorded date, not the last row submitted; backdated purchases are valid.
- Reuse top-level fields as documented summaries for existing sorting and
  templates: `purchase_date` is the latest date, `purchase_weight_grams` is
  cumulative purchased weight, and `purchase_price_total` is cumulative cost
  only when every purchase is priced. `unit_price_per_kg` is the weighted
  lifetime average, also unknown when any price is missing. Label summaries
  clearly so a lifetime average cannot be mistaken for the latest unit price.
- Keep `stock_grams` as the stored balance used by current list filtering and
  roast flows. Atomically update purchase history, summary fields, stock by
  the net purchased-weight difference, and `updated_at`. Reject stale form
  submissions instead of overwriting a newer purchase or roast deduction;
  repeated submissions must not add stock twice.
- Preserve the reconciliation relationship:
  `stock = purchased grams - consumed roast grams + logged corrections + opening adjustment`.
  Consumption includes non-archived roasts that actually started; drafts and
  manually completed drafts without a start do not count. Read-only views must
  not write or repeatedly deduct inventory.
- Preserve RN-0025 zeroing and negative stock. Replace silent direct-stock
  overwrites with a recorded manual correction in the existing stock log.
  Store one `inventory_opening_adjustment_grams` during migration for historical
  differences; do not invent missing purchase events to explain those gaps.
- Purchase changes apply only their weight delta. Roast start/edit/archive
  retain their existing stock timing and maintain the relationship above.
  Fix directly affected accounting gaps: changing beans at equal roast weight
  must transfer consumption, and repeating archive/start must not change stock
  twice. Do not expand into a general roast lifecycle redesign.
- The remaining meter uses cumulative purchased grams, keeps the existing
  0–100 clamp, and retains exact signed stock, sorting, and out-of-stock filters.
- Out of scope: FIFO/lot allocation, per-roast purchase assignment, multiple
  currencies, orders/invoices, supplier history, new reports, automatic merging
  of duplicate bean profiles, multi-device array conflict merging, and applied
  remote database synchronization.

### Local migration and operator handoff

Add `scripts/migrate_bean_purchases.py` with a read-only default/`--dry-run`
mode and an explicit local-only `--apply` mode. Reuse existing configuration
and BSON backup utilities where practical; do not call a mirror to migrate.

1. Inspect local bean fields and active started-roast usage. Report counts and
   malformed records without publishing raw documents or credentials.
2. Back up the local database under ignored `db_backup/` and verify the backup
   before mutation. Operate while local application writes are paused; use
   conditional writes to reject data that changed after inspection.
3. For each unmigrated bean, wrap its existing scalar purchase in one entry,
   retain its identity, metadata, labels, roasts, logs, and exact stock, and set
   the opening adjustment to preserve the reconciliation equation. Preserve
   incomplete legacy values without fabricating history; report unsupported
   malformed records for correction rather than silently coercing them.
4. Set a valid, current `updated_at` on changed beans and backfill missing
   `created_at` without rewriting a valid one. A second run is a no-op and
   must not refresh timestamps, append purchases, or recalculate an established
   opening adjustment. Existing arrays are preserved.
5. Run the migration against the user's local data only after automated and
   browser verification. Record migrated/skipped/conflicted counts, backup
   verification, and before/after stock parity. The user then maintains their
   actual purchase history through the new form.
6. Run a fresh local-to-online sync dry run. Provide the guarded handoff and
   explain newer-destination/missing-timestamp conflicts. Deploy compatible
   application code before copying the new schema online. Whole-bean sync
   retains its existing timestamp policy; it does not merge individual rows.

## Acceptance Criteria

- [x] Two or more purchases share one bean identity and retain the existing
  profile, label, and roast history; users can add and correct purchase rows.
- [x] Date/weight/total-price history, latest date, cumulative weight/cost, and
  weighted unit-price summaries follow the rules above after reload and sorting.
- [x] A 1000g purchase, 200g started roast, and 500g repurchase leave 1300g;
  correcting the repurchase to 600g leaves 1400g; backdating changes neither
  consumption nor which later purchase supplies the latest date.
- [x] Draft/manual completion, roast weight edits, equal-weight bean transfer,
  archive/repeat archive, zeroing, manual correction, and purchase retries
  preserve the documented inventory relationship and signed balances.
- [x] Legacy migration preserves every original stock balance and all unrelated
  bean/roast data; its second run performs no writes. Invalid records are
  reported and not silently discarded or converted into fake purchases.
- [x] The user's local records are backed up, migrated, and verified; the user
  can subsequently enter or correct purchases themselves.
- [x] Embedded purchases, Decimal128 prices, adjustments, and summaries survive
  sync insert/update in fixtures; a configured local-to-online dry run and
  guarded operator handoff are recorded without applying a remote mirror.
- [x] Testing Impact reviewed against the implementation diff; declared automated and browser coverage is complete.
- [x] Documentation Impact reviewed against the implementation diff; every affected document below is updated in this branch.

## Testing Impact

- Change classification: backend-api, ui-interaction, cross-workflow, database-sync
- Browser verification level: full
- Automated tests to add or update: `tests/test_beans_api.py` for array CRUD, input validation, atomic weight deltas, stale/repeated writes, summaries, manual corrections, and legacy compatibility; new `tests/test_bean_purchase_migration.py` for dry-run/no remote client, verified backup before writes, lossless BSON conversion, opening adjustment, invalid-record handling, conditional writes, and idempotency; `tests/test_roasts_api.py` for draft/start/edit/transfer/archive accounting and retries; `tests/test_api_contracts.py` for history, dates, price/stock sorting, remaining meters, signed balances, and empty states; `tests/test_sync_api.py` for complete embedded-array/adjustment round trips and unchanged timestamp conflict rules; `tests/test_management_design_contracts.py` for revised form contracts; `tests/test_database_sync_routes.py` for environment-independent fake database selection. Update `tests/test_app_factory.py` only if the existing form routes cannot be reused.
- Browser E2E scenarios to add or update: `tests/e2e/README.md` -> `Bean`, add `Repeat purchases and inventory reconciliation`, update `Bean Stock Remaining Meter (Targeted)`, and run the complete affected `Live Roast` workflow. Create one bean, start/end a 200g roast, repurchase, edit/backdate/remove a purchase, correct stock, zero/restock, reload, sort/filter, and archive the started roast; verify exact balances/history at each step. Exercise invalid input and stale submission with no data loss. Verify at desktop/mobile widths and preserve the isolated run markers.
- Required commands: `uv run pytest tests/test_beans_api.py tests/test_bean_purchase_migration.py tests/test_roasts_api.py tests/test_api_contracts.py tests/test_sync_api.py tests/test_management_design_contracts.py tests/test_app_factory.py`; `uv run pytest`; `uv run python -m tests.e2e.manage start --run-id rn-0031-purchases-a`; `uv run python -m tests.e2e.manage cleanup --run-id rn-0031-purchases-a`; `uv run python scripts/migrate_bean_purchases.py --dry-run`; after verification and local backup, `uv run python scripts/migrate_bean_purchases.py --apply`, followed by its no-op dry run; `uv run python scripts/sync_database.py --direction local-to-online --dry-run`; `git ls-files db_backup 'db_backup/**'`; `uv run python scripts/generate_issues_index.py`; `uv run python scripts/generate_issues_index.py --check`.
- Required browser evidence: Run IDs `rn-0031-purchases-a` and completion run `rn-0032-confirmations-a`; screenshots of repeatable form, purchase history, latest-date/stock summaries and meter at desktop/mobile widths; exact balance assertions through purchases and roast lifecycle; invalid/stale form behavior; console and failed-network findings; run-scoped cleanup counts in their ignored artifact summaries.
- Not applicable reason: None. Purchase editing changes critical inventory accounting across bean and roast workflows. Migration tests use fixtures or isolated local data; production migration is delivery, never a test or cleanup step.

## Documentation Impact

- `docs/features/beans-management.md`: purchase history, summaries, corrections,
  stock equation, legacy handling, and local migration command/handoff.
- `docs/architecture/data-models.md`: purchase-entry types, summary fields,
  opening adjustment, extended stock-log events, and accounting invariant.
- `docs/architecture/api-endpoints.md`: revised bean form payload, validation,
  concurrency/error responses, and any directly affected roast accounting.
- `docs/design/screens/bean-inventory.md`: repeatable fields, history, summaries,
  correction/removal/error states, and cumulative remaining-meter denominator.
- `docs/features/database-sync.md`: whole-bean purchase sync, timestamps,
  deployment order, local migration versus separately applied remote sync.
- `tests/README.md` and `tests/e2e/README.md`: focused automated coverage and
  affected durable browser scenarios.
- Conditional: `docs/features/live-roasting.md` if a documented roast accounting
  contract changes; `docs/deployment/README.md` for required migration/release
  steps; relevant indexes only if new durable documents are introduced.

## Database Operations Impact

- Collections and local/online effects: migration writes local `beans`, reads
  local `roasts` for opening reconciliation, and preserves all existing `_id`
  references. Ordinary editing writes the selected database. No automatic
  remote migration; the later guarded local-to-online operation copies newer
  complete bean documents, including purchases and corrections.
- Migration or backfill: required local-only, backed-up, idempotent conversion
  of scalar purchases and explicit opening reconciliation; retain stock,
  profile/labels, history, and valid timestamps as specified above.
- Expected sync direction: `local-to-online` after compatible code is available
  remotely and the user has reviewed/edited local purchases. Inspect both
  histories before manual conflict decisions; remote-only roasts must not be
  used to silently recalculate local stock.
- Is an applied mirror part of delivery: No. Delivery includes local migration,
  sync compatibility tests, a fresh read-only forecast, and operator handoff.
  Any later applied mirror needs the separate post-preflight user request and
  both exact run-specific confirmations required by `AGENTS.md`.
- Required backup/audit evidence for resolution: verified ignored local backup,
  migration counts and unchanged balances, idempotent rerun, sanitized evidence
  here, fresh sync forecast and conflict counts, and empty
  `git ls-files db_backup 'db_backup/**'`. Do not commit backup payloads,
  manifests, local raw data, or credentials.

### Planning evidence

- Configured local-to-online dry run `20260915T223625Z-661658b5` succeeded on
  2026-09-15 without writes: 13 source beans and 29 source roasts; forecast one
  bean update, 65 unchanged destination documents, zero timestamp conflicts,
  and 24 destination-only roasts. This is a pre-migration baseline, not proof
  that the new schema is already implemented or synchronized.
- Local inspection was read-only and returned counts only. At planning time no purchase
  migration or applied mirror had run for this ticket; delivery evidence follows.

## Implementation and local delivery evidence

- Implemented embedded purchase forms/history, Decimal summaries, conditional
  bean edits, recorded stock corrections, stock-preserving local migration,
  and directly affected roast start/transfer/archive accounting.
- Full automated suite: `LOCAL_DB_NAME=roastlogger_test_rn0031 uv run pytest -q`
  passed **236 tests** on 2026-09-15. Focused regression suite previously passed
  129 tests. A final full-suite rerun after local delivery also passed all
  **236 tests**. JavaScript syntax, Python compilation, and `git diff --check`
  passed. The fake sync-route fixture pins its fake database name so isolated
  test runs cannot redirect it to a different fake database.
- Browser run `rn-0031-purchases-a` verified creation (1000g), a 200g roast
  start (800g), adding a backdated 500g purchase (1300g), correcting it to 600g
  (1400g), latest-date ordering, a manual correction to 1350g with its -50g
  history, native invalid-weight rejection, and a stale form's inline 409
  with its 700g input retained. Live sensor/event, offline/fault, and recovery
  checks also passed. Desktop and narrow form evidence is in ignored artifacts.
- At initial delivery browser execution was **incomplete**: the in-app browser's native
  confirmation handling stalled at End Roast and populated purchase removal.
  The dialog API reported no active dialog while input commands timed out.
  Remaining removal/cancellation, zero/restock/filtering, end/save/archive,
  sorting, and full responsive/dark checks are not claimed as passed.
  Full-page narrow screenshots also have browser capture artifacts; a viewport
  screenshot shows the stacked purchase controls, but is not full responsive
  sign-off. No confirmation behavior was bypassed or changed to accommodate
  automation. RN-0031 remained in progress until the continuation below.
- Continuation run `rn-0031-purchases-b` prepared isolated fixtures after the
  user dismissed the first popup. The next removal/cancel popup reproduced the
  tool block; no remaining workflow pass is claimed. Its runtime was stopped
  and cleanup removed **1 bean / 1 roast**, with **0 remaining records**.
  Follow-up **RN-0032** tracks the user-requested removal of native confirmation
  popups. The code is delivered with this verification limitation recorded.
- The original isolated runtime was stopped and scoped cleanup passed: **1 bean,
  1 roast, and 2 temperature logs removed; 0 run records remain**. Evidence
  and logs remain ignored under `tests/e2e/artifacts/rn-0031-purchases-a/`.
- Following the user's explicit additional inventory-entry request, local
  delivery proceeded with passing automated migration/accounting coverage,
  browser-verified purchase calculations, and verified backup rather than
  waiting for the confirmation-tool limitation. This is a recorded exception
  to the planned browser-before-local-delivery ordering, not a browser pass.
- Local application writes were paused during backup, migration, and import,
  then resumed. Migration run **`20260915T232137Z-1c0e2309`** verified a complete
  **2-collection / 47-document** local backup, migrated **13 beans**, retained
  **all 13 stock balances**, and reported **0 invalid / 0 conflicts** with
  **3 opening adjustments**. Profiles, notes, corrections, and bean identities
  were checked for parity. An immediate second applied call performed **0
  writes**, with all 13 documents and timestamps unchanged.
- Backup and ignored result records are under
  `db_backup/database_mirrors/local--howie-macbook-pro/roastlogger/20260915T232137Z__20260915T232137Z-1c0e2309/`.
  Manifest SHA-256:
  `62869f9817fec2f36ede82df886c18fe5e1d562055711e54beb3fed64a78d3f5`.
  No raw backup, manifest, receipt, or purchase import result is committed.
- The requested receipt subsequently created **2 beans** and appended **1
  purchase** to an existing bean, increasing total stock by **2000g**. Purchase
  date was supplied by the user. Readback verified each balance and the
  reconciliation equation; the existing purchase row and unrelated beans
  remained unchanged. A final migration preview reports **15 already migrated,
  0 eligible, 0 invalid, 0 conflicts**. The production app is healthy in local
  mode. No remote database write was made.
- Fresh local-to-online dry run **`20260915T232150Z-d3dc9437`** passed:
  **2 bean additions, 13 bean updates, 4 roast additions, 0 timestamp conflicts**.
  It retains 24 destination-only roasts; the other 29 roasts are unchanged.
  The dry run creates no remote backup or audit despite displaying planned
  paths. To sync only bean inventory, use the guarded command below after
  compatible code is deployed online; review a fresh preview and complete both
  confirmations personally. Whole-bean timestamps apply, with no row merging.

```bash
uv run python scripts/sync_database.py --direction local-to-online --collection beans --dry-run
uv run python scripts/sync_database.py --direction local-to-online --collection beans
```

- `git ls-files db_backup 'db_backup/**'` returned no files. Applied remote
  synchronization remains outside this delivery and requires the separately
  authorized guarded flow.

## Resolution

- The implementation, local migration, receipt entry, backup, and configured
  sync preview were delivered as recorded above. The initial automated suite
  passed 236 tests; RN-0032's final full suite passed **242 tests**, including
  the purchase, migration, lifecycle, and sync regression coverage.
- RN-0032 removed the popup blocker and completed browser verification in
  **`rn-0032-confirmations-a`**. Stock followed **1000 -> 800 -> 1300 -> 1400 ->
  1350 -> 750 -> 0 -> 500 -> 700g** through start, repurchase, correction,
  manual adjustment, removal, zeroing, restock, and roast archive. Cancelling
  the unsaved removal retained the saved history and 1350g balance.
- Verified latest-date/history ordering, stock and purchase-date sorting,
  out-of-stock filtering, a cumulative meter of **46.67%** (700/1500), live
  end/save/archive, stock-neutral manual completion, and desktop plus actual
  390 CSS-pixel dark form/Settings views. Earlier invalid-input and stale-form
  checks remain recorded in `rn-0031-purchases-a`; accounting retry cases also
  remain covered by automated tests.
- Final browser console snapshot was empty. Handled concurrent setup/start
  409s and E2E-disabled sync responses are documented in the run summary;
  no popup blocked control. The stopped runtime's scoped cleanup removed
  **2 beans / 3 roasts / 2 temperature logs**, leaving **0 run records**.
- All declared feature, architecture, design, migration/sync, and testing docs
  are updated across the delivery and RN-0032 follow-up. The browser checklist
  now describes direct actions and cancelling the unsaved purchase form.
  Backup payloads remain untracked. No applied remote mirror was performed
  by this implementation or browser run.

## Open Questions

- None blocking implementation. Use total purchase price, weighted lifetime
  summary pricing, and embedded rows as the minimum defaults. Keep independent
  purchase-lot costing and multi-device row reconciliation out of this ticket.

## Related Files

- `models/bean_helpers.py`
- `models/roast_helpers.py`
- `roastlogger/blueprints/beans.py`
- `roastlogger/blueprints/pages.py`
- `roastlogger/blueprints/roasts.py`
- `roastlogger/services/roast_lifecycle.py`
- `roastlogger/services/database_sync.py`
- `roastlogger/services/database_backup.py`
- `templates/beans_form.html`
- `templates/beans_detail.html`
- `templates/beans_list.html`
- Related tickets: RN-0015 (timestamp sync), RN-0025 (zero-stock history),
  RN-0027 (remaining meter), RN-0030 (guarded sync forecast).
