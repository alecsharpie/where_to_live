import uuid
from typing import List, Optional
from app.models.location import LocationModel, LocationCreate, LocationUpdate
from .storage import load_locations_from_gcs, save_locations_to_gcs
import logging

logger = logging.getLogger(__name__)

def create_location(location_data: LocationCreate) -> LocationModel:
    locations = load_locations_from_gcs()

    new_location = LocationModel(
        id=uuid.uuid4(), # Generate new ID here
        name=location_data.name,
        address=location_data.address,
        notes=location_data.notes,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        enrichment_data={} # Initialize empty enrichment data
    )

    locations.append(new_location)
    save_locations_to_gcs(locations)
    logger.info(f"Created new location with ID: {new_location.id} and name: {new_location.name}")
    return new_location

def get_all_locations() -> List[LocationModel]:
    logger.debug("Fetching all locations.")
    return load_locations_from_gcs()

def get_location_by_id(location_id: uuid.UUID) -> Optional[LocationModel]:
    locations = load_locations_from_gcs()
    for loc in locations:
        if loc.id == location_id:
            logger.debug(f"Found location with ID: {location_id}")
            return loc
    logger.debug(f"Location with ID: {location_id} not found.")
    return None

def update_location(location_id: uuid.UUID, location_update_data: LocationUpdate) -> Optional[LocationModel]:
    locations = load_locations_from_gcs()
    location_to_update = None
    updated = False

    for i, loc in enumerate(locations):
        if loc.id == location_id:
            location_to_update = loc
            # Pydantic's model_copy(update=...) is great for this
            update_data_dict = location_update_data.model_dump(exclude_unset=True)
            if update_data_dict: # Check if there's anything to update
                locations[i] = location_to_update.model_copy(update=update_data_dict)
                updated = True
                logger.info(f"Updating location with ID: {location_id}. Changes: {update_data_dict}")
            else:
                logger.info(f"No update data provided for location ID: {location_id}.")
            break

    if location_to_update and updated:
        save_locations_to_gcs(locations)
        logger.info(f"Successfully updated location with ID: {location_id}")
        return locations[i] # Return the updated model
    elif location_to_update and not updated:
        logger.info(f"Location with ID: {location_id} found, but no update data provided.")
        return location_to_update # Return the original model if no changes were made

    logger.warning(f"Update failed: Location with ID {location_id} not found.")
    return None

def delete_location(location_id: uuid.UUID) -> bool:
    locations = load_locations_from_gcs()
    initial_count = len(locations)

    # Filter out the location to be deleted
    locations_after_deletion = [loc for loc in locations if loc.id != location_id]

    if len(locations_after_deletion) < initial_count:
        save_locations_to_gcs(locations_after_deletion)
        logger.info(f"Successfully deleted location with ID: {location_id}")
        return True

    logger.warning(f"Delete failed: Location with ID {location_id} not found.")
    return False
