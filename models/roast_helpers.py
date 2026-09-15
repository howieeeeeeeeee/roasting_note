from datetime import datetime
from bson.objectid import ObjectId
from models.bean_purchases import grams, snapshot_query
from werkzeug.exceptions import BadRequest, Conflict, NotFound
import pytz
import os

# Get timezone configuration
TIMEZONE = os.environ.get('TIMEZONE', 'America/New_York')
local_tz = pytz.timezone(TIMEZONE)

def get_current_time_with_tz():
    """Get current time in local timezone WITH timezone info for database storage"""
    return datetime.now(local_tz)


def create_draft_roast(roasts_collection, markers=None):
    """
    Create a new draft roast document

    Args:
        roasts_collection: MongoDB collection

    Returns:
        ObjectId of created roast
    """
    current_time_utc = get_current_time_with_tz()
    roast_doc = {
        'title': 'Untitled Roast',
        'roast_date': current_time_utc,
        'temp_measurement_method': 'K-Type Sensor V1',
        'roaster': 'Freshroast SR800',
        'ambient_temp_celsius': None,
        'ambient_humidity': None,
        'general_notes': '',
        'key_timings': [],
        'temp_curve': [],
        'reviews': [],
        'lifecycle_status': 'draft',
        'archived': False,
        'created_at': current_time_utc,
        'updated_at': current_time_utc
    }
    roast_doc.update(markers or {})

    result = roasts_collection.insert_one(roast_doc)
    return result.inserted_id


def update_roast(roasts_collection, beans_collection, roast_id, roast_data):
    """
    Update a roast document from the edit form

    This handles changes to original_weight_grams and manages bean stock accordingly

    Args:
        roasts_collection: MongoDB roasts collection
        beans_collection: MongoDB beans collection
        roast_id: String or ObjectId of roast to update
        roast_data: Dictionary with updated roast information
    """
    # Get the existing roast to compare original_weight_grams
    existing_roast = roasts_collection.find_one({'_id': ObjectId(roast_id), 'archived': {'$ne': True}})
    if not existing_roast:
        raise NotFound('Roast not found')

    current_time = get_current_time_with_tz()
    update_doc = {
        'title': roast_data.get('title', 'Untitled Roast'),
        'roaster': roast_data.get('roaster', 'Freshroast SR800'),
        'temp_measurement_method': roast_data.get('temp_measurement_method', 'K-Type Sensor V1'),
        'ambient_temp_celsius': float(roast_data['ambient_temp_celsius']) if roast_data.get('ambient_temp_celsius') else None,
        'ambient_humidity': float(roast_data['ambient_humidity']) if roast_data.get('ambient_humidity') else None,
        'general_notes': roast_data.get('general_notes', ''),
        'updated_at': current_time
    }
    if existing_roast and not isinstance(existing_roast.get('created_at'), datetime):
        update_doc['created_at'] = current_time

    # Handle roast date - keep as local time WITH timezone info
    if roast_data.get('roast_date'):
        try:
            # Try parsing datetime-local format first (YYYY-MM-DDTHH:MM) - this is in local timezone
            local_dt = datetime.strptime(roast_data['roast_date'], '%Y-%m-%dT%H:%M')
            # Localize to local timezone and keep timezone info
            update_doc['roast_date'] = local_tz.localize(local_dt)
        except:
            try:
                # Fallback to date-only format for backwards compatibility
                local_dt = datetime.strptime(roast_data['roast_date'], '%Y-%m-%d')
                update_doc['roast_date'] = local_tz.localize(local_dt)
            except:
                pass

    # Handle bean_id
    old_bean_id = existing_roast.get('bean_id')
    new_bean_id = (ObjectId(roast_data['bean_id']) if roast_data.get('bean_id') else None) if 'bean_id' in roast_data else old_bean_id
    update_doc['bean_id'] = new_bean_id

    # Handle weights
    old_original_weight = existing_roast.get('original_weight_grams', 0)
    new_original_weight = old_original_weight
    new_roasted_weight = None

    if 'original_weight_grams' in roast_data:
        try:
            new_original_weight = grams(roast_data['original_weight_grams'] or 0)
            if new_original_weight < 0:
                raise ValueError('Roast weight cannot be negative')
            update_doc['original_weight_grams'] = new_original_weight
        except ValueError as error:
            raise BadRequest(str(error)) from error

    if roast_data.get('roasted_weight_grams'):
        try:
            new_roasted_weight = int(roast_data['roasted_weight_grams'])
            update_doc['roasted_weight_grams'] = new_roasted_weight
        except:
            pass

    # Calculate weight loss percentage
    if new_original_weight and new_roasted_weight:
        weight_loss = ((new_original_weight - new_roasted_weight) / new_original_weight) * 100
        update_doc['weight_loss_percentage'] = round(weight_loss, 2)

    result = roasts_collection.update_one(snapshot_query(existing_roast), {'$set': update_doc})
    if result.matched_count != 1:
        raise Conflict('Roast changed; refresh and try again')
    if existing_roast.get('roast_start_time'):
        # Apply consumption by bean, including equal-weight transfers.
        changes = {}
        if old_bean_id:
            changes[old_bean_id] = old_original_weight
        if new_bean_id:
            changes[new_bean_id] = changes.get(new_bean_id, 0) - new_original_weight
        for bean_id, delta in changes.items():
            if delta:
                beans_collection.update_one(
                    {'_id': bean_id},
                    {'$inc': {'stock_grams': delta}, '$set': {'updated_at': current_time}},
                )
