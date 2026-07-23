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

if __name__ == '__main__':
    print(f"Starting server on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
