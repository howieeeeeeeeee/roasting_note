"""Migration checks use a uniquely named isolated local database."""
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from bson import json_util
from bson.decimal128 import Decimal128
from bson.objectid import ObjectId

from scripts import migrate_bean_purchases as migration


@pytest.fixture
def migration_db(beans_collection):
    client = beans_collection.database.client
    name = f'roastlogger_migration_test_{uuid4().hex}'
    database = client[name]
    runtime = migration.local_runtime({'DEVICE': 'test', 'LOCAL_DB_NAME': name})
    yield database, runtime, client
    client.drop_database(name)


def legacy_bean(database):
    doc = {'_id': ObjectId(), 'name': 'Migration specimen', 'stock_grams': 350,
           'purchase_weight_grams': 1000, 'purchase_date': datetime(2024, 1, 1),
           'purchase_price_total': Decimal128('45.20'), 'created_at': datetime(2024, 1, 1),
           'updated_at': datetime(2024, 1, 2), 'label': {'name': 'Preserve me'},
           'stock_change_log': [{'change_grams': -50}]}
    database.beans.insert_one(doc)
    database.roasts.insert_one({'bean_id': doc['_id'], 'roast_start_time': datetime(2024, 1, 3),
                                'original_weight_grams': 200, 'archived': False})
    database.roasts.insert_one({'bean_id': doc['_id'], 'lifecycle_status': 'completed',
                                'original_weight_grams': 400})
    return doc


def test_dry_run_backup_lossless_apply_and_noop(migration_db, tmp_path):
    database, runtime, client = migration_db
    before = legacy_bean(database)
    preview = migration.migrate(runtime, client, root=tmp_path)
    assert preview['eligible'] == 1 and preview['opening_adjustments'] == 1
    assert not list(tmp_path.iterdir())
    assert database.beans.find_one({'_id': before['_id']}) == before
    report = migration.migrate(runtime, client, root=tmp_path, apply=True)
    assert report['migrated'] == report['stock_balances_preserved'] == 1
    assert report['backup_verification']['status'] == 'complete'
    after = database.beans.find_one({'_id': before['_id']})
    assert after['stock_grams'] == 350
    assert after['inventory_opening_adjustment_grams'] == -400
    assert after['purchases'][0]['price_total'] == before['purchase_price_total']
    assert after['label'] == before['label'] and after['created_at'] == before['created_at']
    assert after['updated_at'] > before['updated_at']
    manifest = Path(report['backup_path']) / 'manifest.json'
    assert manifest.is_file()
    import json
    entry = next(row for row in json.loads(manifest.read_text())['collections'] if row['name'] == 'beans')
    backed_up = json_util.loads((manifest.parent / entry['filename']).read_text())
    assert backed_up == before
    rerun = migration.migrate(runtime, client, root=tmp_path, apply=True)
    assert rerun['already_migrated'] == 1 and rerun['migrated'] == 0
    assert 'backup_path' not in rerun
    assert database.beans.find_one({'_id': before['_id']}) == after


def test_invalid_records_block_apply_without_backup(migration_db, tmp_path):
    database, runtime, client = migration_db
    before = legacy_bean(database)
    database.beans.insert_one({'purchase_weight_grams': -1})
    report = migration.migrate(runtime, client, root=tmp_path, apply=True)
    assert report['invalid'] == 1 and report['migrated'] == 0
    assert not list(tmp_path.iterdir())
    assert database.beans.find_one({'_id': before['_id']}) == before


def test_backup_verification_failure_prevents_writes(migration_db, tmp_path, monkeypatch):
    database, runtime, client = migration_db
    before = legacy_bean(database)
    def fail(*args):
        raise RuntimeError('Invalid backup')
    monkeypatch.setattr(migration, 'verify_backup_result', fail)
    with pytest.raises(RuntimeError):
        migration.migrate(runtime, client, root=tmp_path, apply=True)
    assert database.beans.find_one({'_id': before['_id']}) == before


def test_intervening_bean_or_roast_update_conflicts(migration_db, tmp_path, monkeypatch):
    database, runtime, client = migration_db
    before = legacy_bean(database)
    verify = migration.verify_backup_result
    def change_after_backup(*args):
        result = verify(*args)
        database.beans.update_one({'_id': before['_id']}, {'$inc': {'stock_grams': 1}})
        return result
    monkeypatch.setattr(migration, 'verify_backup_result', change_after_backup)
    report = migration.migrate(runtime, client, root=tmp_path, apply=True)
    assert report['conflicted'] == 1 and report['migrated'] == 0
    assert 'purchases' not in database.beans.find_one({'_id': before['_id']})


def test_unknown_legacy_values_and_empty_profile(migration_db, tmp_path):
    database, runtime, client = migration_db
    bean_id = database.beans.insert_one({'purchase_weight_grams': 500, 'stock_grams': -20}).inserted_id
    empty_id = database.beans.insert_one({'name': 'No purchases'}).inserted_id
    assert migration.migrate(runtime, client, root=tmp_path, apply=True)['migrated'] == 2
    bean = database.beans.find_one({'_id': bean_id})
    assert bean['purchases'][0]['price_total'] is None
    assert bean['purchases'][0]['purchase_date'] is None
    assert bean['stock_grams'] == -20
    assert database.beans.find_one({'_id': empty_id})['purchases'] == []


@pytest.mark.parametrize('uri', ['mongodb+srv://example.com/', 'mongodb://remote.example/', 'mongodb://localhost:27017,remote:27017/'])
def test_migration_rejects_nonlocal_endpoint(uri):
    with pytest.raises(ValueError):
        migration.local_runtime({'DEVICE': 'test', 'MONGO_URI_LOCAL': uri})
