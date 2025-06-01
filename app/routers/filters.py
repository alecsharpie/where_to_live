import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, status
from pydantic import BaseModel
import googlemaps

from app.models.location import LocationModel
from app.crud import locations as crud_locations
from app.main import _get_google_maps_api_key # Import the getter from main

logger = logging.getLogger(__name__)
router = APIRouter()

class FilterRequest(BaseModel):
    source_address: str
    max_driving_time_minutes: int

class FilteredLocationResponse(LocationModel):
    # This inherits from LocationModel and can add/override fields if needed for the response
    # For now, driving_time_to_target_seconds is already in LocationModel
    pass


def get_maps_client(api_key: str = Depends(_get_google_maps_api_key)):
    if not api_key: # Should be handled by _get_google_maps_api_key raising HTTPException
        raise HTTPException(status_code=500, detail="Maps API key not available.")
    try:
        return googlemaps.Client(key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Google Maps client: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to initialize Maps client.")


@router.post("/filter_by_driving_time", response_model=List[FilteredLocationResponse])
def filter_locations_by_driving_time(
    filter_request: FilterRequest,
    gmaps: googlemaps.Client = Depends(get_maps_client)
):
    logger.info(f"Filtering locations by driving time from '{filter_request.source_address}' within {filter_request.max_driving_time_minutes} minutes.")

    try:
        geocode_result = gmaps.geocode(filter_request.source_address)
        if not geocode_result:
            logger.warn(f"Could not geocode source address: {filter_request.source_address}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not geocode source address: {filter_request.source_address}")

        source_coords = (geocode_result[0]['geometry']['location']['lat'], geocode_result[0]['geometry']['location']['lng'])
        logger.info(f"Source address '{filter_request.source_address}' geocoded to: {source_coords}")

    except Exception as e:
        logger.error(f"Error geocoding source address '{filter_request.source_address}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error geocoding source address. {e}")

    all_locations = crud_locations.get_all_locations()
    if not all_locations:
        logger.info("No locations available to filter.")
        return []

    filtered_locations = []
    max_driving_time_seconds = filter_request.max_driving_time_minutes * 60

    for loc_original in all_locations:
        # Create a copy to avoid modifying the original data in memory/GCS for this transient calculation
        loc = loc_original.model_copy(deep=True)

        if loc.latitude is None or loc.longitude is None:
            logger.info(f"Location '{loc.name}' (ID: {loc.id}) is missing coordinates. Attempting to geocode address: {loc.address}")
            try:
                loc_geocode_result = gmaps.geocode(loc.address)
                if loc_geocode_result:
                    loc.latitude = loc_geocode_result[0]['geometry']['location']['lat']
                    loc.longitude = loc_geocode_result[0]['geometry']['location']['lng']
                    logger.info(f"Geocoded '{loc.name}' to ({loc.latitude}, {loc.longitude}).")
                    # Note: This geocoded result is NOT saved back to GCS by this filter endpoint.
                    # This should be part of the CRUD for locations if persistence of geocoded data is desired.
                else:
                    logger.warning(f"Could not geocode address '{loc.address}' for location '{loc.name}'. Skipping this location for distance calculation.")
                    continue # Skip if cannot geocode
            except Exception as e:
                logger.error(f"Error geocoding address '{loc.address}' for location '{loc.name}': {e}", exc_info=True)
                continue # Skip on error

        if loc.latitude is None or loc.longitude is None: # Check again after attempt
            logger.warning(f"Skipping location '{loc.name}' as it has no coordinates after geocoding attempt.")
            continue

        destination_coords = (loc.latitude, loc.longitude)

        try:
            logger.debug(f"Calculating distance matrix for {source_coords} to {destination_coords} for location '{loc.name}'.")
            matrix = gmaps.distance_matrix(origins=[source_coords], destinations=[destination_coords], mode="driving")

            if matrix['rows'][0]['elements'][0]['status'] == 'OK':
                duration_seconds = matrix['rows'][0]['elements'][0]['duration']['value']
                loc.driving_time_to_target_seconds = duration_seconds # Set on the copy
                logger.info(f"Driving time from '{filter_request.source_address}' to '{loc.name}': {duration_seconds}s.")
                if duration_seconds <= max_driving_time_seconds:
                    filtered_locations.append(FilteredLocationResponse.model_validate(loc)) # Validate before appending
            else:
                status_msg = matrix['rows'][0]['elements'][0]['status']
                logger.warning(f"Distance Matrix API returned status '{status_msg}' for destination '{loc.name}'. Skipping.")

        except Exception as e:
            logger.error(f"Error calculating driving time for location '{loc.name}': {e}", exc_info=True)
            # Decide if you want to skip this location or halt the request
            # For now, skip the location on error to make the endpoint more resilient

    logger.info(f"Found {len(filtered_locations)} locations matching the criteria.")
    return filtered_locations
