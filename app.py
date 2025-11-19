import os
import collections
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128
from dotenv import load_dotenv
import requests

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
# Temperature Sensor Helper Functions
# ============================================

def fetch_temperature_from_sensor_fast():
    """
    Fast single-request temperature fetch for display updates.
    Uses 200ms timeout for reliable response while still being responsive.

    Returns:
        int: Rounded temperature reading, or None if request fails
    """
    TEMP_SENSOR_URL = os.environ.get('TEMP_SENSOR_URL', 'http://192.168.0.47/temp')
    TIMEOUT = 0.2  # 200ms timeout for fast but reliable response

    try:
        response = requests.get(TEMP_SENSOR_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            # Try both field names for compatibility
            temp_celsius = data.get('temperature_celsius') or data.get('temperatur_celsius')
            if temp_celsius is not None:
                return round(float(temp_celsius))
    except (requests.exceptions.RequestException, ValueError, KeyError):
        pass

    return None


def fetch_temperature_from_sensor():
    """
    Fetch temperature from the K-Type sensor with 3-request averaging logic.
    Used for accurate DB logging.

    Makes 3 consecutive requests to the temperature sensor URL.
    Each request has a 0.1 second (100ms) timeout.

    Returns:
        int: Rounded average of the two highest successful readings, or None if fewer than 2 successful readings
    """
    TEMP_SENSOR_URL = os.environ.get('TEMP_SENSOR_URL', 'http://192.168.0.47/temp')
    TIMEOUT = 0.1  # 100ms timeout

    successful_readings = []

    # Make 3 consecutive requests
    for i in range(3):
        try:
            response = requests.get(TEMP_SENSOR_URL, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                # Try both field names for compatibility
                temp_celsius = data.get('temperature_celsius') or data.get('temperatur_celsius')
                if temp_celsius is not None:
                    successful_readings.append(float(temp_celsius))
        except (requests.exceptions.RequestException, ValueError, KeyError):
            # Timeout, connection error, or invalid JSON - mark this request as failed
            pass

    # Need at least 2 successful readings
    if len(successful_readings) < 2:
        return None

    # Sort in descending order and take top 2
    successful_readings.sort(reverse=True)
    top_two = successful_readings[:2]

    # Calculate average and round to nearest integer
    average = sum(top_two) / len(top_two)
    return round(average)


# ============================================
# HTML-Rendering Routes
# ============================================

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 404 errors"""
    return Response(status=204)

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
    """List of all beans with optional filtering and sorting"""
    # Get filter and sort parameters (filter out-of-stock by default)
    filter_out_of_stock = request.args.get('filter_out_of_stock', 'true') == 'true'
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    # Build query
    query = {'archived': {'$ne': True}}
    if filter_out_of_stock:
        query['stock_grams'] = {'$gt': 0}

    # Determine sort direction
    sort_direction = 1 if sort_order == 'asc' else -1

    # Map sort fields
    sort_field_map = {
        'name': 'name',
        'price': 'unit_price_per_kg',
        'date': 'purchase_date',
        'stock': 'stock_grams'
    }
    sort_field = sort_field_map.get(sort_by, 'name')

    beans = list(beans_collection.find(query).sort(sort_field, sort_direction))
    return render_template('beans_list.html', beans=beans,
                         filter_out_of_stock=filter_out_of_stock,
                         sort_by=sort_by, sort_order=sort_order)


@app.route('/beans/add')
def beans_add_form():
    """Show add bean form"""
    return render_template('beans_form.html', bean=None, is_edit=False)


@app.route('/beans/detail/<bean_id>')
def beans_detail(bean_id):
    """View bean details"""
    bean = beans_collection.find_one({'_id': ObjectId(bean_id), 'archived': {'$ne': True}})
    if not bean:
        return "Bean not found", 404

    # Get all roasts for this bean
    roasts = list(roasts_collection.find({
        'bean_id': ObjectId(bean_id),
        'archived': {'$ne': True}
    }).sort('roast_date', -1))

    # Calculate metrics for each roast
    for roast in roasts:
        roast['bean_name'] = bean['name']
        roast['bean_color'] = bean.get('color', '#6B8E6F')

        # Calculate total roast duration
        if roast.get('roast_start_time') and roast.get('roast_end_time'):
            duration = (roast['roast_end_time'] - roast['roast_start_time']).total_seconds()
            roast['total_duration_seconds'] = int(duration)

        # Calculate time after first crack
        if roast.get('key_timings') and roast.get('total_duration_seconds'):
            fc_start = None
            for timing in roast['key_timings']:
                if 'First Crack Start' in timing['event_name']:
                    fc_start = timing['time_seconds']
            if fc_start:
                roast['time_after_fc'] = roast['total_duration_seconds'] - fc_start

    return render_template('beans_detail.html', bean=bean, roasts=roasts)


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
    """End roast timer and log final temperature if available"""
    roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})

    if not roast:
        return jsonify({'success': False, 'error': 'Roast not found'}), 404

    end_time = datetime.now()

    # Calculate elapsed time for final temperature log
    if roast.get('roast_start_time'):
        elapsed_seconds = int((end_time - roast['roast_start_time']).total_seconds())

        # Try to get final temperature reading (single request)
        temperature = fetch_temperature_from_sensor()

        if temperature is not None:
            # Get current fan/power settings from most recent temp_curve entry
            last_fan = 0
            last_power = 0
            if roast.get('temp_curve') and len(roast['temp_curve']) > 0:
                last_entry = roast['temp_curve'][-1]
                last_fan = last_entry.get('fan_setting', 0)
                last_power = last_entry.get('power_setting', 0)

            # Log final temperature reading
            final_temp_event = {
                'time_seconds': elapsed_seconds,
                'temperature': float(temperature),
                'fan_setting': last_fan,
                'power_setting': last_power
            }

            roasts_collection.update_one(
                {'_id': ObjectId(roast_id)},
                {'$push': {'temp_curve': final_temp_event}}
            )

    # Set roast end time
    roasts_collection.update_one(
        {'_id': ObjectId(roast_id)},
        {'$set': {
            'roast_end_time': end_time,
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

    # Handle temperature - auto-fetch from sensor if not provided
    temp_value = data.get('temperature')
    if temp_value is None:
        # Temperature input was empty, try to fetch from sensor
        temp_value = fetch_temperature_from_sensor()

    # Add temperature only if we have a value (either from input or sensor)
    if temp_value is not None:
        timing_event['temperature'] = float(temp_value)

    # Add optional fan and power settings
    if data.get('fan_setting') is not None:
        timing_event['fan_setting'] = int(data['fan_setting'])
    if data.get('power_setting') is not None:
        timing_event['power_setting'] = int(data['power_setting'])

    # Calculate and add RoR
    if temp_value is not None:
        ror = calculate_ror(roast_id, float(temp_value), int(data['time_seconds']))
        if ror is not None:
            timing_event['ror'] = ror

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
    """Add temperature/settings event to temp_curve array and optionally log to local CSV"""
    data = request.get_json()
    roast = roasts_collection.find_one({'_id': ObjectId(roast_id)})

    # Get fan and power settings, with default values if not provided and no previous events
    fan_setting = data.get('fan_setting')
    power_setting = data.get('power_setting')

    # If fan or power not provided, check for previous events
    if fan_setting is None or power_setting is None:
        # Check if there are any previous events in temp_curve
        if roast and roast.get('temp_curve') and len(roast['temp_curve']) > 0:
            # Use values from most recent event
            last_event = roast['temp_curve'][-1]
            if fan_setting is None:
                fan_setting = last_event.get('fan_setting', 9)
            if power_setting is None:
                power_setting = last_event.get('power_setting', 3)
        else:
            # No previous events, use defaults: fan 9, power 3
            if fan_setting is None:
                fan_setting = 9
            if power_setting is None:
                power_setting = 3
        
        # Ensure they are integers if we fell back to defaults
        if fan_setting is None: fan_setting = 9
        if power_setting is None: power_setting = 3

    temp_event = {
        'time_seconds': int(data['time_seconds']),
        'fan_setting': int(fan_setting),
        'power_setting': int(power_setting)
    }

    # Add temperature only if provided (not None/null)
    if data.get('temperature') is not None:
        temp_event['temperature'] = float(data['temperature'])

    # Add RoR (Rate of Rise)
    # First check if provided in data (legacy), otherwise calculate it
    if data.get('ror') is not None:
        temp_event['ror'] = float(data['ror'])
    elif data.get('temperature') is not None:
        ror = calculate_ror(roast_id, float(data['temperature']), int(data['time_seconds']))
        if ror is not None:
            temp_event['ror'] = ror

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


@app.route('/api/roast/log_temp_local/<roast_id>', methods=['POST'])
def api_roast_log_temp_local(roast_id):
    """Log temperature reading to local file for detailed analysis"""
    import os

    data = request.get_json()
    time_seconds = data.get('time_seconds')
    temperature = data.get('temperature')
    ror = data.get('ror')  # Rate of Rise

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'temp_logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Create log file named by roast_id
    log_file = os.path.join(logs_dir, f'{roast_id}.csv')

    # Write header if file doesn't exist
    file_exists = os.path.exists(log_file)

    with open(log_file, 'a') as f:
        if not file_exists:
            f.write('time_seconds,temperature,ror\n')
        # Write RoR if available, otherwise write empty field
        ror_value = f'{ror}' if ror is not None else ''
        f.write(f'{time_seconds},{temperature},{ror_value}\n')

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
# API Routes - Temperature Sensor
# ============================================

@app.route('/api/temp/current_fast', methods=['GET'])
def api_temp_current_fast():
    """
    Get current temperature from K-Type sensor (fast single request for display)

    Returns:
        JSON with temperature value (int) or null if sensor unavailable
        {
            "temperature": 190,  // or null
            "status": "success"  // or "error"
        }
    """
    temperature = fetch_temperature_from_sensor_fast()

    if temperature is not None:
        return jsonify({
            'temperature': temperature,
            'status': 'success'
        })
    else:
        return jsonify({
            'temperature': None,
            'status': 'error'
        })


@app.route('/api/temp/current', methods=['GET'])
def api_temp_current():
    """
    Get current temperature from K-Type sensor (accurate 3-request average for DB logging)

    Returns:
        JSON with temperature value (int) or null if sensor unavailable
        {
            "temperature": 190,  // or null
            "status": "success"  // or "error"
            "message": "..."     // optional error message
        }
    """
    temperature = fetch_temperature_from_sensor()

    if temperature is not None:
        return jsonify({
            'temperature': temperature,
            'status': 'success'
        })
    else:
        return jsonify({
            'temperature': None,
            'status': 'error',
            'message': 'Insufficient readings or sensor unavailable'
        })


# ============================================
# Optimized Polling Logic
# ============================================

# Global in-memory storage for recent temperature readings
# Structure: { roast_id: deque([(time, temp), ...], maxlen=30) }
from collections import deque
roast_temp_history = {}

def calculate_ror(roast_id, current_temp, current_time):
    """
    Calculate Rate of Rise (RoR) based on temperature history.
    RoR = (Current Temp - Temp 30s ago) * (60 / 30) = (Delta) * 2
    Returns None if insufficient data.
    """
    if roast_id not in roast_temp_history:
        roast_temp_history[roast_id] = {
            'history': collections.deque(maxlen=60), # Keep last 60 readings
            'last_db_log_time': -1
        }
    
    state = roast_temp_history[roast_id]
    history = state['history']
    
    # Add current reading
    history.append({'time': current_time, 'temp': current_temp})
    
    # Find reading ~30 seconds ago
    target_time = current_time - 30
    past_reading = None
    
    # Search for reading closest to target_time
    # Since deque is ordered by time, we can iterate
    for reading in history:
        if reading['time'] >= target_time:
            # If we found a reading that is exactly or just after target_time
            # Check if it's within a reasonable window (e.g., +/- 2 seconds of target)
            if reading['time'] <= target_time + 2:
                past_reading = reading
            break
            
    if past_reading:
        temp_diff = current_temp - past_reading['temp']
        time_diff = current_time - past_reading['time']
        
        if time_diff > 0:
            # Normalize to per minute
            ror = (temp_diff / time_diff) * 60
            return round(ror, 1)
            
    return None


@app.route('/api/roast/sync_state/<roast_id>', methods=['POST'])
def api_roast_sync_state(roast_id):
    """
    Consolidated endpoint for real-time roast synchronization.
    Called every 1 second by client.
    Handles:
    1. Temperature fetching (Fast vs Accurate)
    2. RoR Calculation
    3. Local CSV Logging (Every 1s)
    4. MongoDB Logging (Every 5s)
    """
    data = request.get_json()
    client_time = int(data.get('time_seconds', 0))
    status = data.get('status', 'stopped')
    fan_setting = int(data.get('fan_setting', 0))
    power_setting = int(data.get('power_setting', 0))

    # Initialize state if needed
    if roast_id not in roast_temp_history:
        roast_temp_history[roast_id] = {
            'history': collections.deque(maxlen=60),
            'last_db_log_time': -1
        }
    
    state = roast_temp_history[roast_id]

    # Determine if we should log to DB based on time interval
    # Log if we crossed a 5-second boundary since last log
    # e.g., last=10, current=16 -> 16//5 (3) > 10//5 (2) -> Log
    # e.g., last=10, current=14 -> 14//5 (2) == 10//5 (2) -> No log
    current_interval = client_time // 5
    last_interval = state['last_db_log_time'] // 5
    is_db_log_interval = (current_interval > last_interval) and (client_time > 0)

    # Fetch temperature
    # Use accurate fetch if it's a DB log interval, otherwise fast fetch
    if is_db_log_interval:
        temp = fetch_temperature_from_sensor()
    else:
        temp = fetch_temperature_from_sensor_fast()

    response_data = {
        'success': True,
        'temperature': temp,
        'ror': None,
        'logged_to_db': False
    }

    if temp is not None:
        # Calculate RoR
        ror = calculate_ror(roast_id, temp, client_time)
        response_data['ror'] = ror

        # If roast is running, handle logging
        if status == 'running':
            # 1. Log to local CSV (Always)
            try:
                logs_dir = os.path.join(os.getcwd(), 'temp_logs')
                os.makedirs(logs_dir, exist_ok=True)
                log_file = os.path.join(logs_dir, f'{roast_id}.csv')
                
                file_exists = os.path.exists(log_file)
                with open(log_file, 'a') as f:
                    if not file_exists:
                        f.write('time_seconds,temperature,ror\n')
                    ror_str = str(ror) if ror is not None else ''
                    f.write(f'{client_time},{temp},{ror_str}\n')
            except Exception as e:
                print(f"Error logging local CSV: {e}")

            # 2. Log to MongoDB (Every 5 seconds)
            if is_db_log_interval:
                try:
                    temp_event = {
                        'time_seconds': client_time,
                        'temperature': float(temp),
                        'fan_setting': fan_setting,
                        'power_setting': power_setting,
                        'ror': ror
                    }
                    roasts_collection.update_one(
                        {'_id': ObjectId(roast_id)},
                        {
                            '$push': {'temp_curve': temp_event},
                            '$set': {'updated_at': datetime.now()}
                        }
                    )
                    response_data['logged_to_db'] = True
                    # Update last log time
                    state['last_db_log_time'] = client_time
                except Exception as e:
                    print(f"Error logging to MongoDB: {e}")

    return jsonify(response_data)


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
