import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# MongoDB Connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client.roastlogger

# Collections
beans_collection = db.beans
roasts_collection = db.roasts


# ============================================
# HTML-Rendering Routes
# ============================================

@app.route('/')
def index():
    """Dashboard - list of all roasts"""
    roasts = list(roasts_collection.find({'archived': {'$ne': True}}).sort('roast_date', -1))

    # Get bean names and calculate metrics for each roast
    for roast in roasts:
        if roast.get('bean_id'):
            bean = beans_collection.find_one({'_id': ObjectId(roast['bean_id'])})
            if bean:
                roast['bean_name'] = bean['name']
                roast['bean_color'] = bean.get('color', '#6B8E6F')
            else:
                roast['bean_name'] = 'Unknown Bean'
                roast['bean_color'] = '#6B8E6F'
        else:
            roast['bean_name'] = 'Not Set'
            roast['bean_color'] = '#6B8E6F'

        # Calculate total roast duration
        if roast.get('roast_start_time') and roast.get('roast_end_time'):
            duration = (roast['roast_end_time'] - roast['roast_start_time']).total_seconds()
            roast['total_duration_seconds'] = int(duration)

        # Calculate time after first crack (use latest FC if multiple)
        if roast.get('key_timings') and roast.get('total_duration_seconds'):
            fc_start = None
            # Find the latest First Crack Start
            for timing in roast['key_timings']:
                if 'First Crack Start' in timing['event_name']:
                    fc_start = timing['time_seconds']  # Will keep updating to latest one
            if fc_start:
                roast['time_after_fc'] = roast['total_duration_seconds'] - fc_start

    return render_template('index.html', roasts=roasts)


@app.route('/beans')
def beans_list():
    """List of all beans"""
    beans = list(beans_collection.find({'archived': {'$ne': True}}).sort('name', 1))
    return render_template('beans_list.html', beans=beans)


@app.route('/beans/add')
def beans_add_form():
    """Show add bean form"""
    return render_template('beans_form.html', bean=None, is_edit=False)


@app.route('/beans/edit/<bean_id>')
def beans_edit_form(bean_id):
    """Show edit bean form"""
    bean = beans_collection.find_one({'_id': ObjectId(bean_id), 'archived': {'$ne': True}})
    if not bean:
        return "Bean not found", 404
    return render_template('beans_form.html', bean=bean, is_edit=True)


@app.route('/roast/new')
def roast_new():
    """Create new draft roast and redirect to live interface"""
    from models.roast_helpers import create_draft_roast
    new_roast_id = create_draft_roast(roasts_collection)
    return redirect(url_for('roast_live', roast_id=new_roast_id))


@app.route('/roast/live/<roast_id>')
def roast_live(roast_id):
    """Live roasting interface"""
    roast = roasts_collection.find_one({'_id': ObjectId(roast_id), 'archived': {'$ne': True}})
    if not roast:
        return "Roast not found", 404

    beans = list(beans_collection.find({'archived': {'$ne': True}}).sort('name', 1))
    return render_template('roast_live.html', roast=roast, beans=beans)


@app.route('/roast/detail/<roast_id>')
def roast_detail(roast_id):
    """View roast details"""
    roast = roasts_collection.find_one({'_id': ObjectId(roast_id), 'archived': {'$ne': True}})
    if not roast:
        return "Roast not found", 404

    # Get bean info
    if roast.get('bean_id'):
        bean = beans_collection.find_one({'_id': ObjectId(roast['bean_id'])})
        roast['bean_name'] = bean['name'] if bean else 'Unknown Bean'
    else:
        roast['bean_name'] = 'Not Set'

    # Calculate duration if start and end times exist
    if roast.get('roast_start_time') and roast.get('roast_end_time'):
        duration = (roast['roast_end_time'] - roast['roast_start_time']).total_seconds()
        roast['roast_duration_seconds'] = int(duration)

    return render_template('roast_detail.html', roast=roast)


@app.route('/roast/edit/<roast_id>')
def roast_edit_form(roast_id):
    """Edit roast form"""
    roast = roasts_collection.find_one({'_id': ObjectId(roast_id), 'archived': {'$ne': True}})
    if not roast:
        return "Roast not found", 404

    beans = list(beans_collection.find({'archived': {'$ne': True}}).sort('name', 1))
    return render_template('roast_edit.html', roast=roast, beans=beans)


# ============================================
# API Routes - Beans
# ============================================

@app.route('/api/beans/add', methods=['POST'])
def api_beans_add():
    """Add new bean"""
    from models.bean_helpers import create_bean
    bean_data = request.form.to_dict()
    bean_id = create_bean(beans_collection, bean_data)
    return redirect(url_for('beans_list'))


@app.route('/api/beans/edit/<bean_id>', methods=['POST'])
def api_beans_edit(bean_id):
    """Edit bean"""
    from models.bean_helpers import update_bean
    bean_data = request.form.to_dict()
    update_bean(beans_collection, bean_id, bean_data)
    return redirect(url_for('beans_list'))


@app.route('/api/beans/delete/<bean_id>', methods=['POST'])
def api_beans_delete(bean_id):
    """Archive bean (soft delete)"""
    beans_collection.update_one(
        {'_id': ObjectId(bean_id)},
        {'$set': {
            'archived': True,
            'updated_at': datetime.now()
        }}
    )
    return redirect(url_for('beans_list'))


# ============================================
# API Routes - Roasts
# ============================================

@app.route('/api/roast/create', methods=['POST'])
def api_roast_create():
    """Create new draft roast"""
    from models.roast_helpers import create_draft_roast
    new_roast_id = create_draft_roast(roasts_collection)
    return jsonify({'new_roast_id': str(new_roast_id)})


@app.route('/api/roast/start/<roast_id>', methods=['POST'])
def api_roast_start(roast_id):
    """Start roast timer"""
    data = request.get_json() or {}

    update_data = {
        'roast_start_time': datetime.now(),
        'updated_at': datetime.now()
    }

    # Update bean_id and original_weight if provided
    if data.get('bean_id'):
        update_data['bean_id'] = ObjectId(data['bean_id'])
    if data.get('original_weight_grams'):
        update_data['original_weight_grams'] = int(data['original_weight_grams'])

        # Decrement bean stock
        if data.get('bean_id'):
            beans_collection.update_one(
                {'_id': ObjectId(data['bean_id'])},
                {'$inc': {'stock_grams': -int(data['original_weight_grams'])}}
            )

    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {'$set': update_data}
    )

    return jsonify({'success': True})


@app.route('/api/roast/end/<roast_id>', methods=['POST'])
def api_roast_end(roast_id):
    """End roast timer"""
    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {'$set': {
            'roast_end_time': datetime.now(),
            'updated_at': datetime.now()
        }}
    )
    return jsonify({'success': True})


@app.route('/api/roast/update_title/<roast_id>', methods=['POST'])
def api_roast_update_title(roast_id):
    """Update roast title"""
    data = request.get_json()
    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {'$set': {
            'title': data.get('title', 'Untitled Roast'),
            'updated_at': datetime.now()
        }}
    )
    return jsonify({'success': True})


@app.route('/api/roast/add_timing/<roast_id>', methods=['POST'])
def api_roast_add_timing(roast_id):
    """Add timing event to key_timings array with optional temp/fan/power"""
    data = request.get_json()

    timing_event = {
        'event_name': data['event_name'],
        'time_seconds': int(data['time_seconds'])
    }

    # Add optional temperature, fan, and power settings
    if data.get('temperature') is not None:
        timing_event['temperature'] = float(data['temperature'])
    if data.get('fan_setting') is not None:
        timing_event['fan_setting'] = int(data['fan_setting'])
    if data.get('power_setting') is not None:
        timing_event['power_setting'] = int(data['power_setting'])

    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {
            '$push': {'key_timings': timing_event},
            '$set': {'updated_at': datetime.now()}
        }
    )

    return jsonify({'success': True})


@app.route('/api/roast/add_event/<roast_id>', methods=['POST'])
def api_roast_add_event(roast_id):
    """Add temperature/settings event to temp_curve array"""
    data = request.get_json()

    temp_event = {
        'time_seconds': int(data['time_seconds']),
        'temperature': float(data['temperature']),
        'fan_setting': int(data.get('fan_setting', 0)),
        'power_setting': int(data.get('power_setting', 0))
    }

    # Add note if provided
    if data.get('note'):
        temp_event['note'] = data['note']

    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {
            '$push': {'temp_curve': temp_event},
            '$set': {'updated_at': datetime.now()}
        }
    )

    return jsonify({'success': True})


@app.route('/api/roast/update/<roast_id>', methods=['POST'])
def api_roast_update(roast_id):
    """Update roast from edit form"""
    from models.roast_helpers import update_roast
    roast_data = request.form.to_dict()
    update_roast(roasts_collection, beans_collection, roast_id, roast_data)
    return redirect(url_for('roast_detail', roast_id=roast_id))


@app.route('/api/roast/delete/<roast_id>', methods=['POST'])
def api_roast_delete(roast_id):
    """Archive roast (soft delete) and restore bean stock"""
    roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})

    # Restore bean stock if applicable
    if roast and roast.get('bean_id') and roast.get('original_weight_grams'):
        beans_collection.update_one(
            {'_id': ObjectId(roast['bean_id'])},
            {'$inc': {'stock_grams': roast['original_weight_grams']}}
        )

    # Archive the roast instead of deleting
    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {'$set': {
            'archived': True,
            'updated_at': datetime.now()
        }}
    )
    return redirect(url_for('index'))


@app.route('/api/roast/add_review/<roast_id>', methods=['POST'])
def api_roast_add_review(roast_id):
    """Add review to roast"""
    data = request.get_json() or request.form.to_dict()

    review = {
        '_id': ObjectId(),
        'overall_score': int(data.get('overall_score', 3)),
        'extraction_method': data.get('extraction_method', ''),
        'notes': data.get('notes', ''),
        'review_date': datetime.now(),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {
            '$push': {'reviews': review},
            '$set': {'updated_at': datetime.now()}
        }
    )

    if request.is_json:
        return jsonify({'success': True, 'review_id': str(review['_id'])})
    else:
        return redirect(url_for('roast_detail', roast_id=roast_id))


@app.route('/api/roast/update_review/<roast_id>/<review_id>', methods=['POST'])
def api_roast_update_review(roast_id, review_id):
    """Update an existing review"""
    data = request.get_json() or request.form.to_dict()

    # Build the update for the specific review in the array
    update_fields = {
        'reviews.$.overall_score': int(data.get('overall_score', 3)),
        'reviews.$.extraction_method': data.get('extraction_method', ''),
        'reviews.$.notes': data.get('notes', ''),
        'reviews.$.updated_at': datetime.now(),
        'updated_at': datetime.now()
    }

    roasts_collection.update_one(
        {'_id': ObjectId(roast_id), 'reviews._id': ObjectId(review_id)},
        {'$set': update_fields}
    )

    if request.is_json:
        return jsonify({'success': True})
    else:
        return redirect(url_for('roast_detail', roast_id=roast_id))


@app.route('/api/roast/delete_review/<roast_id>/<review_id>', methods=['POST'])
def api_roast_delete_review(roast_id, review_id):
    """Delete a review from the roast"""
    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {
            '$pull': {'reviews': {'_id': ObjectId(review_id)}},
            '$set': {'updated_at': datetime.now()}
        }
    )

    if request.is_json:
        return jsonify({'success': True})
    else:
        return redirect(url_for('roast_detail', roast_id=roast_id))


# ============================================
# Template Filters
# ============================================

@app.template_filter('format_date')
def format_date(value):
    """Format datetime for display"""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return str(value)


@app.template_filter('format_seconds')
def format_seconds(seconds):
    """Format seconds as MM:SS"""
    if seconds is None:
        return ''
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
