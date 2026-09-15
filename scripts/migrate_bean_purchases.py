"""Back up and convert local bean purchases; default execution is read-only."""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.bean_purchases import migration_fields, snapshot_query
from roastlogger.services.database_backup import backup_destination_database, verify_backup_result
from roastlogger.services.database_sync_plan import (
    SyncRuntime, new_run_id, validate_database_name, validate_device,
)


def local_runtime(values):
    uri = values.get('MONGO_URI_LOCAL', 'mongodb://localhost:27017/')
    parsed = urlsplit(uri)
    if parsed.scheme != 'mongodb' or ',' in parsed.netloc or parsed.hostname not in {'localhost', '127.0.0.1', '::1'}:
        raise ValueError('Migration requires a loopback local MongoDB endpoint')
    database = validate_database_name(values.get('LOCAL_DB_NAME', 'roastlogger'))
    return SyncRuntime(
        direction='local-migration', device=validate_device(values.get('DEVICE')),
        batch_size=500, requested_collections=('beans',),
        source_role='local', destination_role='local', source_uri=uri,
        destination_uri=uri, source_database_name=database, destination_database_name=database,
    )


def plan_migration(database):
    plans = []
    counts = Counter(eligible=0, already_migrated=0, invalid=0, opening_adjustments=0)
    errors = Counter()
    for bean in database.beans.find({'test_data': {'$ne': True}}):
        try:
            fields = migration_fields(bean, database.roasts)
            if fields is None:
                counts['already_migrated'] += 1
                continue
            plans.append((bean, fields))
            counts['eligible'] += 1
            counts['opening_adjustments'] += fields['inventory_opening_adjustment_grams'] != 0
        except (ValueError, TypeError, KeyError):
            counts['invalid'] += 1
            errors['Unsupported legacy purchase, stock, or history; inspect locally'] += 1
    return plans, {**counts, 'errors': dict(errors)}


def migrate(runtime, client, *, root=ROOT, apply=False):
    database = client[runtime.destination_database_name]
    plans, counts = plan_migration(database)
    report = {'mode': 'apply' if apply else 'dry-run', 'database': runtime.destination_database_name,
              **counts, 'migrated': 0, 'conflicted': 0, 'stock_balances_preserved': 0}
    if not apply or not plans or counts['invalid']:
        return report
    run_id = new_run_id()
    backup = backup_destination_database(runtime, client, root, run_id)
    verification = verify_backup_result(runtime, root, run_id, backup)
    report.update(run_id=run_id, backup_path=backup['path'], backup_verification=verification)
    try:
        for bean, fields in plans:
            # Recheck consumption after the backup as well as the bean snapshot.
            if migration_fields(bean, database.roasts) != fields:
                report['conflicted'] += 1
                continue
            now = datetime.now(timezone.utc)
            fields = {**fields, 'updated_at': now}
            if not isinstance(bean.get('created_at'), datetime):
                fields['created_at'] = now
            result = database.beans.update_one(snapshot_query(bean), {'$set': fields})
            if result.matched_count != 1:
                report['conflicted'] += 1
                continue
            report['migrated'] += 1
            after = database.beans.find_one({'_id': bean['_id']})
            if after['stock_grams'] != bean.get('stock_grams', 0):
                raise RuntimeError('Post-migration balance changed')
            report['stock_balances_preserved'] += 1
        report['status'] = 'conflict' if report['conflicted'] else 'success'
    except Exception:
        report['status'] = 'failed'
        raise
    finally:
        # Sanitized counts stay beside the ignored, verified BSON backup.
        (Path(backup['path']) / 'purchase-migration-result.json').write_text(
            json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--apply', action='store_true', help='Back up and migrate local beans; pause local application writes first')
    args = parser.parse_args(argv)
    try:
        values = {**dotenv_values(ROOT / '.env'), **os.environ}
        runtime = local_runtime(values)
        # This script never constructs an online client.
        with MongoClient(runtime.destination_uri, serverSelectionTimeoutMS=5000, directConnection=True) as client:
            client.admin.command('ping')
            result = migrate(runtime, client, apply=args.apply)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result['invalid'] or result['conflicted'] else 0
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__,
                          'message': 'Local migration failed; inspect the local backup and diagnostics.'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
