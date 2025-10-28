from datetime import datetime
from bson.objectid import ObjectId


def create_draft_roast(roasts_collection):
    """
    Create a new draft roast document

    Args:
        roasts_collection: MongoDB collection

    Returns:
        ObjectId of created roast
    """
    roast_doc = {
        'title': 'Untitled Roast',
        'roast_date': datetime.now(),
        'temp_measurement_method': '',
        'general_notes': '',
        'key_timings': [],
        'temp_curve': [],
        'reviews': [],
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

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
    existing_roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})

    update_doc = {
        'title': roast_data.get('title', 'Untitled Roast'),
        'temp_measurement_method': roast_data.get('temp_measurement_method', ''),
        'general_notes': roast_data.get('general_notes', ''),
        'updated_at': datetime.now()
    }

    # Handle roast date
    if roast_data.get('roast_date'):
        try:
            update_doc['roast_date'] = datetime.strptime(roast_data['roast_date'], '%Y-%m-%d')
        except:
            pass

    # Handle bean_id
    old_bean_id = existing_roast.get('bean_id')
    new_bean_id = roast_data.get('bean_id')

    if new_bean_id:
        update_doc['bean_id'] = ObjectId(new_bean_id)

    # Handle weights
    old_original_weight = existing_roast.get('original_weight_grams', 0)
    new_original_weight = 0
    new_roasted_weight = None

    if roast_data.get('original_weight_grams'):
        try:
            new_original_weight = int(roast_data['original_weight_grams'])
            update_doc['original_weight_grams'] = new_original_weight
        except:
            pass

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

    # Update bean stock if original_weight_grams changed
    if new_original_weight != old_original_weight:
        weight_difference = new_original_weight - old_original_weight

        # If bean changed, handle both old and new beans
        if old_bean_id and new_bean_id and str(old_bean_id) != str(new_bean_id):
            # Restore stock to old bean
            if old_original_weight > 0:
                beans_collection.update_one(
                    {'_id': ObjectId(old_bean_id)},
                    {'$inc': {'stock_grams': old_original_weight}}
                )
            # Deduct stock from new bean
            if new_original_weight > 0:
                beans_collection.update_one(
                    {'_id': ObjectId(new_bean_id)},
                    {'$inc': {'stock_grams': -new_original_weight}}
                )
        elif new_bean_id:
            # Same bean, just adjust the difference
            beans_collection.update_one(
                {'_id': ObjectId(new_bean_id)},
                {'$inc': {'stock_grams': -weight_difference}}
            )

    # Update the roast
    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {'$set': update_doc}
    )
