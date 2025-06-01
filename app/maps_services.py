import googlemaps
import os
from datetime import datetime

# Attempt to load the API key from an environment variable
# For local development, you might set this in your shell or a .env file (not committed)
# For GCP deployment (e.g., Cloud Run, App Engine), set it as an environment variable in the service configuration.
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

if not GOOGLE_MAPS_API_KEY:
    print("WARNING: GOOGLE_MAPS_API_KEY environment variable not set. Google Maps integration will not work.")
    gmaps = None
else:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

def get_geocode(address):
    """
    Geocodes an address to latitude and longitude.
    Returns (lat, lng) or None if not found or API error.
    """
    if not gmaps:
        print("Google Maps client not initialized. Cannot geocode.")
        return None
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result and len(geocode_result) > 0:
            location = geocode_result[0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            return None
    except Exception as e:
        print(f"Error during geocoding: {e}")
        return None

def get_driving_time(origin_address, destination_address, departure_time='now'):
    """
    Calculates the driving time between two addresses.
    departure_time can be 'now' or a specific datetime object.
    Returns duration in seconds, or None if an error occurs.
    """
    if not gmaps:
        print("Google Maps client not initialized. Cannot calculate driving time.")
        return None
    try:
        if departure_time == 'now':
            dep_time = datetime.now()
        else:
            dep_time = departure_time

        directions_result = gmaps.directions(origin_address,
                                             destination_address,
                                             mode="driving",
                                             departure_time=dep_time)
        if directions_result and len(directions_result) > 0:
            # Duration is in seconds
            duration_seconds = directions_result[0]['legs'][0]['duration']['value']
            # You can also get 'duration_in_traffic' if available and relevant
            # duration_text = directions_result[0]['legs'][0]['duration']['text']
            return duration_seconds
        else:
            return None
    except Exception as e:
        print(f"Error calculating driving time: {e}")
        return None

def find_places_nearby(location_lat_lng, keyword, radius_meters=50000): # 50km radius
    """
    Finds places (like towns, cities) near a given lat/lng.
    Returns a list of place results or None.
    """
    if not gmaps:
        print("Google Maps client not initialized. Cannot find places.")
        return None
    try:
        places_result = gmaps.places_nearby(location=location_lat_lng,
                                            keyword=keyword,
                                            radius=radius_meters,
                                            type='locality') # 'locality' often corresponds to towns/cities
        return places_result.get('results', [])
    except Exception as e:
        print(f"Error finding places nearby: {e}")
        return None

if __name__ == '__main__':
    # Simple test (requires GOOGLE_MAPS_API_KEY to be set)
    if not GOOGLE_MAPS_API_KEY:
        print("Please set the GOOGLE_MAPS_API_KEY environment variable to run tests.")
    else:
        print("Testing Google Maps Service...")
        test_address = "1600 Amphitheatre Parkway, Mountain View, CA"
        print(f"Geocoding '{test_address}'...")
        lat_lng = get_geocode(test_address)
        if lat_lng:
            print(f"Coordinates: {lat_lng}")

            # Test driving time
            origin = "San Francisco, CA"
            destination = "San Jose, CA"
            print(f"Calculating driving time from '{origin}' to '{destination}'...")
            duration = get_driving_time(origin, destination)
            if duration:
                print(f"Driving time: {duration // 60} minutes ({duration} seconds)")
            else:
                print("Could not calculate driving time.")

            # Test find places (using the geocoded location from above)
            print(f"Finding towns/cities near {lat_lng}...")
            places = find_places_nearby(lat_lng, keyword="town", radius_meters=50000)
            if places is not None:
                print(f"Found {len(places)} places:")
                for place in places[:5]: # Print first 5
                    print(f"- {place.get('name')}, Types: {place.get('types')}")
            else:
                print("Could not find places nearby.")

        else:
            print(f"Could not geocode '{test_address}'.")
