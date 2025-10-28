from datetime import datetime
from bson.decimal128 import Decimal128


def create_bean(beans_collection, bean_data):
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
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

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
    from bson.objectid import ObjectId

    # Parse and prepare update data
    update_doc = {
        'name': bean_data.get('name', ''),
        'origin': bean_data.get('origin', ''),
        'process': bean_data.get('process', ''),
        'supplier': bean_data.get('supplier', ''),
        'notes': bean_data.get('notes', ''),
        'updated_at': datetime.now()
    }

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
