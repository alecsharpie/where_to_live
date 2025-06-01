import json
import os
from typing import List, Dict, Any
from google.cloud import storage
from app.models.location import LocationModel
import logging

logger = logging.getLogger(__name__)

_gcs_client = None

def _get_gcs_client() -> storage.Client:
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client()
    return _gcs_client

def _get_bucket_name() -> str:
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME environment variable not set.")
        raise ValueError("GCS_BUCKET_NAME not set")
    return bucket_name

def _get_data_blob_name() -> str:
    blob_name = os.environ.get("GCS_DATA_BLOB_NAME", "locations.json") # Default to locations.json
    if not blob_name: # Should not happen with default
        logger.error("GCS_DATA_BLOB_NAME environment variable issue.")
        raise ValueError("GCS_DATA_BLOB_NAME not set effectively")
    return blob_name

def load_locations_from_gcs() -> List[LocationModel]:
    client = _get_gcs_client()
    bucket_name = _get_bucket_name()
    blob_name = _get_data_blob_name()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    try:
        if not blob.exists():
            logger.info(f"Data blob {blob_name} not found in bucket {bucket_name}. Returning empty list.")
            return []

        json_data = blob.download_as_string()
        if not json_data: # Handle empty file case
             logger.info(f"Data blob {blob_name} is empty. Returning empty list.")
             return []

        data = json.loads(json_data)
        # Ensure data is a list before parsing
        if not isinstance(data, list):
            logger.error(f"Data in {blob_name} is not a list. Found: {type(data)}")
            # Depending on desired robustness, either raise error or return empty / try to recover
            return [] # Or raise ValueError("Invalid data format: expected a list of locations")

        locations = [LocationModel.model_validate(item) for item in data]
        logger.info(f"Successfully loaded {len(locations)} locations from GCS: gs://{bucket_name}/{blob_name}")
        return locations
    except Exception as e:
        logger.error(f"Error loading locations from GCS (gs://{bucket_name}/{blob_name}): {e}", exc_info=True)
        # Depending on desired behavior, could raise error or return empty list
        # For robustness in a system that might have transient GCS issues or malformed data:
        return [] # Or re-raise the exception if it's critical path and should halt

def save_locations_to_gcs(locations: List[LocationModel]) -> None:
    client = _get_gcs_client()
    bucket_name = _get_bucket_name()
    blob_name = _get_data_blob_name()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Serialize with Pydantic's model_dump for proper handling of UUIDs, etc.
    data_to_save = [loc.model_dump(mode='json') for loc in locations]
    json_data = json.dumps(data_to_save, indent=2)

    try:
        blob.upload_from_string(json_data, content_type="application/json")
        logger.info(f"Successfully saved {len(locations)} locations to GCS: gs://{bucket_name}/{blob_name}")
    except Exception as e:
        logger.error(f"Error saving locations to GCS (gs://{bucket_name}/{blob_name}): {e}", exc_info=True)
        raise # Re-raise after logging, as saving is often a critical path
