from datetime import datetime
from bson.objectid import ObjectId

from roastlogger.time_utils import get_current_time_with_tz
from models.bean_purchases import (
    BeanConflict, bean_version, grams, legacy_purchases, migration_fields,
    parse_purchases, purchase_summaries, snapshot_query,
)


def normalize_short_flavor_notes(value):
    """Return short flavor notes as a clean list of non-empty strings."""
    if value is None:
        return []

    if isinstance(value, list):
        raw_notes = value
    else:
        raw_notes = str(value).replace("\r\n", "\n").replace("\r", "\n").split("\n")

    notes = []
    seen = set()
    for note in raw_notes:
        cleaned = str(note).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        notes.append(cleaned)
    return notes


def _profile_fields(data, existing=None):
    existing = existing or {}
    fields = {key: data.get(key, existing.get(key, '')) for key in
              ('name', 'origin', 'process', 'supplier', 'notes', 'color')}
    fields['name'] = fields['name'].strip()
    if not fields['name']:
        raise ValueError('Bean name is required')
    fields['color'] = fields['color'] or '#6B8E6F'
    fields['short_flavor_notes'] = normalize_short_flavor_notes(
        data.get('short_flavor_notes', existing.get('short_flavor_notes')))
    return fields


def create_bean(beans_collection, bean_data, markers=None):
    purchases = parse_purchases(bean_data)
    summaries = purchase_summaries(purchases)
    stock = summaries['purchase_weight_grams']
    correction = bean_data.get('stock_grams', '')
    if correction != '':
        stock = grams(correction, 'Stock')
    now = get_current_time_with_tz()
    doc = {
        **_profile_fields(bean_data), **summaries,
        'purchases': purchases, 'stock_grams': stock,
        'inventory_opening_adjustment_grams': stock - summaries['purchase_weight_grams'],
        'stock_change_log': [], 'archived': False,
        'created_at': now, 'updated_at': now,
        **(markers or {}),
    }
    return beans_collection.insert_one(doc).inserted_id


def update_bean(beans_collection, bean_id, bean_data, roasts_collection):
    bean = beans_collection.find_one({'_id': ObjectId(bean_id), 'archived': {'$ne': True}})
    if not bean:
        raise LookupError('Bean not found')
    if bean_data.get('bean_version') != bean_version(bean):
        raise BeanConflict('This bean changed. Reload the page before saving; your entries are still shown.')
    old_purchases = legacy_purchases(bean)
    purchases = parse_purchases(bean_data, old_purchases) if 'purchase_history' in bean_data else old_purchases
    summaries = purchase_summaries(purchases)
    delta = summaries['purchase_weight_grams'] - purchase_summaries(old_purchases)['purchase_weight_grams']
    previous_stock = grams(bean.get('stock_grams', 0), 'Stock')
    stock = grams(previous_stock + delta, 'Stock')
    correction = bean_data.get('stock_grams', '')
    corrected_stock = grams(correction, 'Stock') if correction != '' else stock
    now = get_current_time_with_tz()
    updates = {
        **(migration_fields(bean, roasts_collection) or {}),
        **_profile_fields(bean_data, bean), **summaries,
        'purchases': purchases, 'stock_grams': corrected_stock, 'updated_at': now,
    }
    if not isinstance(bean.get('created_at'), datetime):
        updates['created_at'] = now
    operation = {'$set': updates}
    if corrected_stock != stock:
        operation['$push'] = {'stock_change_log': {
            'event_type': 'manual_correction', 'previous_stock_grams': stock,
            'change_grams': corrected_stock - stock,
            'resulting_stock_grams': corrected_stock, 'recorded_at': now,
        }}
    result = beans_collection.update_one(snapshot_query(bean), operation)
    if result.matched_count != 1:
        raise BeanConflict('This bean changed. Reload the page before saving; your entries are still shown.')


def set_bean_stock_to_zero(beans_collection, bean_id):
    object_id = ObjectId(bean_id)
    active_query = {'_id': object_id, 'archived': {'$ne': True}}
    bean = beans_collection.find_one(active_query)
    if not bean:
        return {'status': 'not_found'}

    previous_stock = bean.get('stock_grams', 0)
    if previous_stock == 0:
        return {'status': 'already_zero'}
    if not isinstance(previous_stock, int) or isinstance(previous_stock, bool):
        return {'status': 'conflict'}

    recorded_at = get_current_time_with_tz()
    stock_change = {
        'event_type': 'set_to_zero',
        'previous_stock_grams': previous_stock,
        'change_grams': -previous_stock,
        'resulting_stock_grams': 0,
        'recorded_at': recorded_at,
    }
    result = beans_collection.update_one(
        {**active_query, 'stock_grams': previous_stock},
        {
            '$set': {'stock_grams': 0, 'updated_at': recorded_at},
            '$push': {'stock_change_log': stock_change},
        },
    )
    if result.modified_count == 1:
        return {
            'status': 'success',
            'previous_stock_grams': previous_stock,
            'change_grams': -previous_stock,
            'stock_grams': 0,
            'stock_change': stock_change,
        }

    current_bean = beans_collection.find_one(active_query)
    if not current_bean:
        return {'status': 'not_found'}
    if current_bean.get('stock_grams', 0) == 0:
        return {'status': 'already_zero'}
    return {'status': 'conflict'}
