from flask import Flask, render_template, request, jsonify
import db
import config

app = Flask(__name__)
app.config.from_object(config)

# Initialize database schema on startup
with app.app_context():
    try:
        db.init_db()
    except Exception as e:
        print(f"Error initializing DB on startup: {e}")

@app.route('/')
def index():
    """Serves the main application page."""
    return render_template('index.html')

@app.route('/share/<ride_id>')
def share_ride(ride_id):
    """Renders a simplified mobile-friendly preview of a specific ride for public sharing."""
    try:
        ride = db.get_ride_by_id(ride_id)
        if ride:
            return render_template('share.html', ride=ride)
        else:
            return "Ride invoice not found", 404
    except Exception as e:
        return f"Error loading share page: {str(e)}", 500

@app.route('/api/rides', methods=['GET'])
def get_rides():
    """API endpoint to retrieve all saved rides."""
    try:
        rides = db.get_all_rides()
        return jsonify({
            'success': True,
            'count': len(rides),
            'rides': rides
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rides/<ride_id>', methods=['GET'])
def get_ride(ride_id):
    """API endpoint to retrieve a single ride by ID."""
    try:
        ride = db.get_ride_by_id(ride_id)
        if ride:
            return jsonify({
                'success': True,
                'ride': ride
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Ride not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rides', methods=['POST'])
def create_ride():
    """API endpoint to save a new ride."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing JSON payload'
            }), 400

        # Required fields check
        required_fields = [
            'ride_id', 'customer_name', 'time_of_ride', 'distance_km', 'duration_min',
            'pickup_address', 'drop_address', 'total_amount', 'ride_charge', 'booking_fees',
            'convenience_charges', 'gateway_charges', 'payment_method', 'captain_name', 'vehicle_number',
            'invoice_no', 'state', 'captain_fee', 'ride_cgst', 'ride_sgst',
            'booking_cgst', 'booking_sgst'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Save to DB
        db.save_ride(data)
        
        # Auto sync ride to daily timeline
        try:
            time_str = str(data.get('time_of_ride', ''))
            travel_date = time_str.split('T')[0] if 'T' in time_str else (time_str.split(' ')[0] if ' ' in time_str else '2026-07-01')
            time_part = time_str.split('T')[1][:5] if 'T' in time_str and len(time_str.split('T')) > 1 else '09:00 AM'
            db.save_travel_log({
                'travel_date': travel_date,
                'start_time': time_part,
                'log_type': 'travel',
                'title': f"Ride with {data.get('captain_name', 'Captain')}",
                'subtitle': f"Invoice #{data.get('invoice_no', '')}",
                'mode': 'car',
                'distance_km': data.get('distance_km', 0),
                'duration_min': data.get('duration_min', 0),
                'pickup_address': data.get('pickup_address', ''),
                'drop_address': data.get('drop_address', ''),
                'ride_id': data.get('ride_id', '')
            })
        except Exception as sync_err:
            print(f"Timeline auto-sync warning: {sync_err}")

        return jsonify({
            'success': True,
            'message': 'Ride saved successfully',
            'ride_id': data['ride_id']
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rides/<ride_id>', methods=['DELETE'])
def delete_ride(ride_id):
    """API endpoint to delete a ride."""
    try:
        success = db.delete_ride(ride_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Ride deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Ride not found or could not be deleted'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timeline', methods=['GET'])
def get_timeline():
    """API endpoint to retrieve daily travel timeline logs."""
    try:
        travel_date = request.args.get('date', '2026-07-01')
        logs = db.get_timeline_by_date(travel_date)
        return jsonify({
            'success': True,
            'date': travel_date,
            'count': len(logs),
            'logs': logs
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timeline', methods=['POST'])
def save_timeline():
    """API endpoint to add or update a travel timeline record."""
    try:
        data = request.get_json()
        if not data or not data.get('travel_date') or not data.get('title'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: travel_date, title'
            }), 400

        log_id = db.save_travel_log(data)
        return jsonify({
            'success': True,
            'message': 'Timeline log saved successfully',
            'log_id': log_id
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timeline/insights', methods=['GET'])
def get_timeline_insights():
    """API endpoint to get summary insights & mode breakdowns for a date."""
    try:
        travel_date = request.args.get('date', '2026-07-01')
        insights = db.get_timeline_insights(travel_date)
        return jsonify({
            'success': True,
            'insights': insights
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timeline/places', methods=['GET'])
def get_timeline_places():
    """API endpoint to retrieve saved places repository across all dates."""
    try:
        places = db.get_all_timeline_places()
        return jsonify({
            'success': True,
            'count': len(places),
            'places': places
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timeline/gps', methods=['POST'])
def save_gps_timeline():
    """API endpoint to save live GPS location entry to daily routine timeline."""
    try:
        data = request.get_json()
        if not data or not data.get('lat') or not data.get('lng'):
            return jsonify({
                'success': False,
                'error': 'Missing lat or lng coordinates'
            }), 400

        import datetime
        now = datetime.datetime.now()
        travel_date = data.get('travel_date') or now.strftime('%Y-%m-%d')
        start_time = now.strftime('%I:%M %p')

        payload = {
            'log_id': f"GPS_{int(now.timestamp() * 1000)}",
            'travel_date': travel_date,
            'start_time': start_time,
            'end_time': start_time,
            'log_type': 'stop',
            'title': data.get('title') or 'Current Location (GPS)',
            'subtitle': data.get('address') or f"Lat: {data['lat']}, Lng: {data['lng']}",
            'mode': 'other',
            'distance_km': 0.0,
            'duration_min': 0.0,
            'pickup_address': data.get('address') or f"Lat: {data['lat']}, Lng: {data['lng']}",
            'pickup_lat': float(data['lat']),
            'pickup_lng': float(data['lng'])
        }

        log_id = db.save_travel_log(payload)
        return jsonify({
            'success': True,
            'message': 'GPS location saved to timeline routine',
            'log': payload
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timeline/<log_id>', methods=['DELETE'])
def delete_timeline(log_id):
    """API endpoint to delete a timeline record."""
    try:
        success = db.delete_travel_log(log_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Timeline entry deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Entry not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Starting server on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


