"""Embedded purchase validation, summaries, and legacy inventory reconciliation."""

import hashlib
import re
from datetime import datetime
from decimal import Decimal, DecimalException, localcontext

from bson import json_util
from bson.decimal128 import Decimal128, create_decimal128_context
from bson.objectid import ObjectId


class BeanConflict(ValueError):
    pass


def bean_version(bean):
    return hashlib.sha256(json_util.dumps(bean, sort_keys=True).encode()).hexdigest()


def snapshot_query(document):
    """Match the complete observed document so intervening writes win."""
    return {'_id': document['_id'], '$expr': {'$eq': ['$$ROOT', {'$literal': document}]}}


def grams(value, label='Weight', *, positive=False):
    if isinstance(value, bool) or not re.fullmatch(r'-?\d+', str(value)):
        raise ValueError(f'{label} must be whole grams')
    result = int(value)
    if abs(result) > 2**53 - 1 or (positive and result <= 0):
        raise ValueError(f'{label} must be a positive, supported weight' if positive else f'{label} is too large')
    return result


def price(value):
    if value in (None, ''):
        return None
    try:
        amount = value.to_decimal() if isinstance(value, Decimal128) else Decimal(str(value))
        if not amount.is_finite() or amount < 0:
            raise ValueError('Total price must be a finite nonnegative number')
        return Decimal128(amount)
    except (DecimalException, TypeError, ValueError) as error:
        raise ValueError('Total price must be a finite nonnegative number') from error


def purchase_date(value):
    if value in (None, ''):
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Purchase date must use YYYY-MM-DD')
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except ValueError as error:
        raise ValueError('Purchase date must be a valid calendar date') from error


def legacy_purchases(bean):
    """Project one old purchase without writing or inventing missing history."""
    if 'purchases' in bean:
        if not isinstance(bean['purchases'], list):
            raise ValueError('Existing purchase history must be an array')
        return bean['purchases']
    fields = ('purchase_date', 'purchase_weight_grams', 'purchase_price_total')
    if not any(bean.get(key) is not None for key in fields):
        return []
    return [{
        'id': bean['_id'],
        'purchase_date': purchase_date(bean.get('purchase_date')),
        'weight_grams': grams(bean.get('purchase_weight_grams'), positive=True),
        'price_total': price(bean.get('purchase_price_total')),
    }]


def parse_purchases(form, existing=()):
    """Read repeated native form fields; a completely blank new row is optional."""
    keys = ('purchase_id', 'purchase_date', 'purchase_weight_grams', 'purchase_price_total')
    values = [form.getlist(key) for key in keys]
    row_count = max(map(len, values), default=0)
    values = [value if value else [''] * row_count for value in values]
    if len({len(value) for value in values}) != 1:
        raise ValueError('Purchase rows are incomplete; reload and try again')
    allowed_ids = {str(row['id']) for row in existing}
    seen = set()
    purchases = []
    for identifier, date, weight, amount in zip(*values):
        if not any((identifier, date, weight, amount)):
            continue
        if identifier:
            if not ObjectId.is_valid(identifier) or identifier not in allowed_ids or identifier in seen:
                raise ValueError('Purchase row has an invalid or duplicate identifier')
            row_id = ObjectId(identifier)
            seen.add(identifier)
        else:
            row_id = ObjectId()
        purchases.append({
            'id': row_id,
            'purchase_date': purchase_date(date),
            'weight_grams': grams(weight, positive=True),
            'price_total': price(amount),
        })
    return purchases


def purchase_summaries(purchases):
    total_weight = sum(row['weight_grams'] for row in purchases)
    grams(total_weight)
    dates = [row['purchase_date'] for row in purchases if row.get('purchase_date')]
    total_price = unit_price = None
    if purchases and all(row.get('price_total') is not None for row in purchases):
        with localcontext(create_decimal128_context()):
            total = sum((row['price_total'].to_decimal() for row in purchases), Decimal(0))
            total_price = price(total)
            unit_price = price(total * 1000 / total_weight) if total_weight else None
    return {
        'purchase_date': max(dates, key=lambda value: value.strftime('%Y-%m-%d')) if dates else None,
        'purchase_weight_grams': total_weight,
        'purchase_price_total': total_price,
        'unit_price_per_kg': unit_price,
    }


def consumed_grams(roasts, bean_id):
    return sum(grams(roast.get('original_weight_grams', 0)) for roast in roasts.find({
        'bean_id': bean_id, 'archived': {'$ne': True},
        'roast_start_time': {'$type': 'date'},
    }))


def migration_fields(bean, roasts):
    if 'purchases' in bean:
        if not isinstance(bean['purchases'], list):
            raise ValueError('Existing purchase history must be an array')
        return None
    purchases = legacy_purchases(bean)
    summaries = purchase_summaries(purchases)
    stock = grams(bean.get('stock_grams', 0), 'Stock')
    log = bean.get('stock_change_log', [])
    if not isinstance(log, list):
        raise ValueError('Stock history must be an array')
    corrections = sum(grams(row['change_grams'], 'Stock correction') for row in log)
    return {
        'purchases': purchases,
        **summaries,
        'stock_grams': stock,
        'inventory_opening_adjustment_grams': (
            stock - summaries['purchase_weight_grams'] + consumed_grams(roasts, bean['_id']) - corrections
        ),
    }


def purchase_view(bean):
    """Render legacy documents too; unsupported history stays untouched."""
    try:
        purchases = legacy_purchases(bean)
    except (ValueError, TypeError, KeyError):
        return []
    result = []
    for row in purchases:
        summary = purchase_summaries([row])
        result.append({**row, 'unit_price_per_kg': summary['unit_price_per_kg']})
    return sorted(result, key=lambda row: row['purchase_date'].strftime('%Y-%m-%d') if row.get('purchase_date') else '', reverse=True)
