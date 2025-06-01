from flask import jsonify, request, render_template
from . import main
from .. import db # Assuming db is initialized in app/__init__.py
from ..models import PotentialLocation
from ..maps_services import get_geocode, get_driving_time # For geocoding and driving time calculation

# Helper to convert text to boolean
def to_boolean(value):
    return str(value).lower() in ['true', '1', 't', 'y', 'yes']

@main.route('/api/locations', methods=['POST'])
def create_location():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    name = data.get('name')
    if not name:
        return jsonify({"error": "Name is required"}), 400

    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # If address is provided but no lat/lng, try to geocode
    if address and (latitude is None or longitude is None):
        print(f"Attempting to geocode address: {address}")
        coordinates = get_geocode(address)
        if coordinates:
            latitude, longitude = coordinates
            print(f"Geocoded successfully: Lat={latitude}, Lng={longitude}")
        else:
            print(f"Failed to geocode address: {address}")
            # Decide if you want to fail or create without lat/lng
            # For now, let's allow creation without lat/lng if geocoding fails
            pass


    new_location = PotentialLocation(
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
        reference_address=data.get('reference_address'),
        driving_time_seconds=data.get('driving_time_seconds'),
        driving_time_text=data.get('driving_time_text'),
        population=data.get('population'),
        wikipedia_url=data.get('wikipedia_url'),
        notes=data.get('notes')
    )

    db.session.add(new_location)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500

    return jsonify(new_location.to_dict()), 201

@main.route('/api/locations', methods=['GET'])
def get_locations():
    locations = PotentialLocation.query.all()
    return jsonify([location.to_dict() for location in locations]), 200

@main.route('/api/locations/<int:id>', methods=['GET'])
def get_location(id):
    location = PotentialLocation.query.get_or_404(id)
    return jsonify(location.to_dict()), 200

@main.route('/api/locations/<int:id>', methods=['PUT'])
def update_location(id):
    location = PotentialLocation.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    location.name = data.get('name', location.name)
    original_address = location.address
    new_address = data.get('address', location.address)

    latitude = data.get('latitude', location.latitude)
    longitude = data.get('longitude', location.longitude)

    # If address changed, or if lat/lng are missing, try to geocode
    if new_address and (new_address != original_address or latitude is None or longitude is None):
        print(f"Address changed or lat/lng missing. Attempting to geocode new address: {new_address}")
        coordinates = get_geocode(new_address)
        if coordinates:
            latitude, longitude = coordinates
            print(f"Geocoded successfully: Lat={latitude}, Lng={longitude}")
        else:
            print(f"Failed to geocode address: {new_address}")
            # Keep old lat/lng if geocoding fails for an *update* unless explicitly cleared
            if latitude is None and 'latitude' not in data: # if latitude was not in payload
                 latitude = location.latitude # keep old
            if longitude is None and 'longitude' not in data: # if longitude was not in payload
                 longitude = location.longitude # keep old


    location.address = new_address
    location.latitude = latitude
    location.longitude = longitude

    location.reference_address = data.get('reference_address', location.reference_address)
    location.driving_time_seconds = data.get('driving_time_seconds', location.driving_time_seconds)
    location.driving_time_text = data.get('driving_time_text', location.driving_time_text)
    location.population = data.get('population', location.population)
    location.wikipedia_url = data.get('wikipedia_url', location.wikipedia_url)
    location.notes = data.get('notes', location.notes)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500

    return jsonify(location.to_dict()), 200

@main.route('/api/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    location = PotentialLocation.query.get_or_404(id)
    db.session.delete(location)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "message": str(e)}), 500
    return jsonify({'message': 'Location deleted successfully'}), 200

# The existing health check route
@main.route('/api/health', methods=['GET'])
def health_check():
    # Basic health check:
    health_info = {'status': 'ok'}
    # Database connectivity check:
    try:
        db.session.execute('SELECT 1')
        health_info['database_status'] = 'ok'
    except Exception as e:
        health_info['database_status'] = 'error'
        health_info['database_message'] = str(e)
        # Potentially return 503 if DB is critical, but for now just report
    return jsonify(health_info)


# New endpoint for calculating and saving driving time
@main.route('/api/locations/<int:id>/calculate_driving_time', methods=['POST'])
def calculate_and_save_driving_time(id):
    location = PotentialLocation.query.get_or_404(id)
    data = request.get_json()
    if not data or 'origin_address' not in data:
        return jsonify({"error": "origin_address is required in payload"}), 400

    origin_address = data['origin_address']

    if not location.address and (not location.latitude or not location.longitude):
        return jsonify({"error": "Location has no address or coordinates to calculate driving time to."}), 400

    destination_identifier = location.address
    if not destination_identifier: # Fallback to lat/lng if no address
        destination_identifier = f"{location.latitude},{location.longitude}"

    print(f"Calculating driving time from '{origin_address}' to '{destination_identifier}' for location ID {id}")

    duration_seconds = get_driving_time(origin_address, destination_identifier)

    if duration_seconds is not None:
        location.reference_address = origin_address
        location.driving_time_seconds = duration_seconds
        # Simple conversion to hours and minutes for the text representation
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        location.driving_time_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        try:
            db.session.commit()
            print(f"Successfully saved driving time for location ID {id}")
            return jsonify(location.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            print(f"Database error while saving driving time for location ID {id}: {e}")
            return jsonify({"error": "Database error", "message": str(e)}), 500
    else:
        print(f"Failed to calculate driving time from '{origin_address}' to '{destination_identifier}' for location ID {id}")
        return jsonify({"error": "Failed to calculate driving time using Google Maps API"}), 500

@main.route('/')
def map_page():
    return render_template('map.html')

@main.route('/admin')
def admin_page():
    return render_template('admin.html')
