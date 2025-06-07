import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.location import LocationModel, LocationCreate, LocationUpdate
from app.crud import locations as crud_locations
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/locations", response_model=LocationModel, status_code=status.HTTP_201_CREATED)
def create_new_location(location_data: LocationCreate):
    try:
        logger.info(f"Attempting to create location: {location_data.name}")
        created_location = crud_locations.create_location(location_data)
        logger.info(f"Successfully created location ID {created_location.id} with name {created_location.name}")
        return created_location
    except ValueError as ve: # Catch specific errors from CRUD if any defined
        logger.error(f"ValueError during location creation: {ve}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error creating location {location_data.name}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while creating location.")


@router.get("/locations", response_model=List[LocationModel])
def read_all_locations():
    try:
        logger.info("Fetching all locations.")
        all_locations = crud_locations.get_all_locations()
        logger.info(f"Retrieved {len(all_locations)} locations.")
        return all_locations
    except Exception as e:
        logger.error(f"Error reading all locations: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while fetching locations.")


@router.get("/locations/{location_id}", response_model=LocationModel)
def read_location_by_id(location_id: uuid.UUID):
    logger.info(f"Fetching location with ID: {location_id}")
    location = crud_locations.get_location_by_id(location_id)
    if location is None:
        logger.warning(f"Location with ID {location_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    logger.info(f"Successfully fetched location ID {location_id}.")
    return location


@router.put("/locations/{location_id}", response_model=LocationModel)
def update_existing_location(location_id: uuid.UUID, location_update_data: LocationUpdate):
    logger.info(f"Attempting to update location ID: {location_id}")
    updated_location = crud_locations.update_location(location_id, location_update_data)
    if updated_location is None:
        logger.warning(f"Update failed: Location with ID {location_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found for update")
    logger.info(f"Successfully updated location ID {location_id}.")
    return updated_location


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_location(location_id: uuid.UUID):
    logger.info(f"Attempting to delete location ID: {location_id}")
    deleted = crud_locations.delete_location(location_id)
    if not deleted:
        logger.warning(f"Deletion failed: Location with ID {location_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found for deletion")
    logger.info(f"Successfully deleted location ID {location_id}.")
    return None # Return None for 204 No Content
