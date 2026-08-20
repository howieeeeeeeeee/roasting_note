from datetime import datetime
from bson.decimal128 import Decimal128
from bson.objectid import ObjectId

from roastlogger.time_utils import get_current_time_with_tz


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


def create_bean(beans_collection, bean_data, markers=None):
    """
    Create a new bean document

    Args:
        beans_collection: MongoDB collection
        bean_data: Dictionary with bean information from form

    Returns:
        ObjectId of created bean
    """
    # Parse and prepare bean document
    bean_doc = {
        'name': bean_data.get('name', ''),
        'origin': bean_data.get('origin', ''),
        'process': bean_data.get('process', ''),
        'supplier': bean_data.get('supplier', ''),
        'notes': bean_data.get('notes', ''),
        'short_flavor_notes': normalize_short_flavor_notes(
            bean_data.get('short_flavor_notes')
        ),
        'stock_change_log': [],
        'color': bean_data.get('color', '#6B8E6F'),  # Default: muted green
        'archived': False,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    bean_doc.update(markers or {})

    # Handle date
    if bean_data.get('purchase_date'):
        try:
            bean_doc['purchase_date'] = datetime.strptime(bean_data['purchase_date'], '%Y-%m-%d')
        except:
            bean_doc['purchase_date'] = None

    # Handle numeric fields
    if bean_data.get('purchase_price_total'):
        try:
            bean_doc['purchase_price_total'] = Decimal128(bean_data['purchase_price_total'])
        except:
            bean_doc['purchase_price_total'] = Decimal128('0')

    if bean_data.get('purchase_weight_grams'):
        try:
            bean_doc['purchase_weight_grams'] = int(bean_data['purchase_weight_grams'])
        except:
            bean_doc['purchase_weight_grams'] = 0

    if bean_data.get('stock_grams'):
        try:
            bean_doc['stock_grams'] = int(bean_data['stock_grams'])
        except:
            bean_doc['stock_grams'] = 0

    # Calculate unit price per kg if possible
    if bean_doc.get('purchase_price_total') and bean_doc.get('purchase_weight_grams'):
        try:
            weight_kg = bean_doc['purchase_weight_grams'] / 1000.0
            if weight_kg > 0:
                price_float = float(bean_doc['purchase_price_total'].to_decimal())
                unit_price = price_float / weight_kg
                bean_doc['unit_price_per_kg'] = Decimal128(str(unit_price))
        except:
            pass

    result = beans_collection.insert_one(bean_doc)
    return result.inserted_id


def update_bean(beans_collection, bean_id, bean_data):
    """
    Update an existing bean document

    Args:
        beans_collection: MongoDB collection
        bean_id: String or ObjectId of bean to update
        bean_data: Dictionary with updated bean information
    """
    current_time = datetime.now()
    existing_bean = beans_collection.find_one({'_id': ObjectId(bean_id)})

    # Parse and prepare update data
    update_doc = {
        'name': bean_data.get('name', ''),
        'origin': bean_data.get('origin', ''),
        'process': bean_data.get('process', ''),
        'supplier': bean_data.get('supplier', ''),
        'notes': bean_data.get('notes', ''),
        'short_flavor_notes': normalize_short_flavor_notes(
            bean_data.get('short_flavor_notes')
        ),
        'color': bean_data.get('color', '#6B8E6F'),
        'updated_at': current_time
    }
    if existing_bean and not isinstance(existing_bean.get('created_at'), datetime):
        update_doc['created_at'] = current_time

    # Handle date
    if bean_data.get('purchase_date'):
        try:
            update_doc['purchase_date'] = datetime.strptime(bean_data['purchase_date'], '%Y-%m-%d')
        except:
            pass

    # Handle numeric fields
    if bean_data.get('purchase_price_total'):
        try:
            update_doc['purchase_price_total'] = Decimal128(bean_data['purchase_price_total'])
        except:
            update_doc['purchase_price_total'] = Decimal128('0')

    if bean_data.get('purchase_weight_grams'):
        try:
            update_doc['purchase_weight_grams'] = int(bean_data['purchase_weight_grams'])
        except:
            pass

    if bean_data.get('stock_grams'):
        try:
            update_doc['stock_grams'] = int(bean_data['stock_grams'])
        except:
            pass

    # Calculate unit price per kg if possible
    if update_doc.get('purchase_price_total') and update_doc.get('purchase_weight_grams'):
        try:
            weight_kg = update_doc['purchase_weight_grams'] / 1000.0
            if weight_kg > 0:
                price_float = float(update_doc['purchase_price_total'].to_decimal())
                unit_price = price_float / weight_kg
                update_doc['unit_price_per_kg'] = Decimal128(str(unit_price))
        except:
            pass

    beans_collection.update_one(
        {'_id': ObjectId(bean_id)},
        {'$set': update_doc}
    )


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
