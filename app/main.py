import os
import logging
from fastapi import FastAPI, HTTPException
from google.cloud import secretmanager
from app.routers import locations, filters # Will create these router files next

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Where To Live NZ API",
    description="API for managing and filtering potential locations in New Zealand.",
    version="0.1.0"
)

_google_maps_api_key = None

def _get_google_maps_api_key() -> str:
    global _google_maps_api_key
    if _google_maps_api_key:
        return _google_maps_api_key

    secret_name = os.environ.get("GOOGLE_MAPS_API_KEY_SECRET_NAME")
    if not secret_name:
        logger.error("GOOGLE_MAPS_API_KEY_SECRET_NAME environment variable is not set.")
        raise HTTPException(status_code=500, detail="Server configuration error: Maps API key secret name not set.")

    try:
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_name)
        _google_maps_api_key = response.payload.data.decode("UTF-8")
        logger.info("Successfully retrieved Google Maps API key from Secret Manager.")
        return _google_maps_api_key
    except Exception as e:
        logger.error(f"Failed to retrieve Google Maps API key from Secret Manager ({secret_name}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server configuration error: Could not access Maps API key. Error: {e}")

# Make the API key available to other modules if needed (e.g. routers)
# A common way is to add it to app.state or use dependency injection.
# For simplicity in this step, routers can import this function or app instance.
app.state.get_google_maps_api_key = _get_google_maps_api_key


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup...")
    # You can preload the key on startup if desired, or let it load on first request.
    # For now, it loads on first request to _get_google_maps_api_key.
    # Test GCS connectivity (optional, but good for early failure detection)
    try:
        from app.crud.storage import _get_bucket_name # To check env var
        _get_bucket_name()
        logger.info(f"GCS_BUCKET_NAME is set.")
    except ValueError as e:
        logger.error(f"Startup check failed: {e}", exc_info=True)
        # Depending on policy, you might want to prevent startup if essential config is missing
        # For now, just log it. The app will fail later if GCS is actually used without config.

    # Test Secret Manager connectivity (optional)
    # try:
    #     _get_google_maps_api_key()
    # except HTTPException as e:
    #    logger.error(f"Startup check failed: Could not retrieve Maps API Key. {e.detail}")
    # Calling it here would make it fail startup if not configured, which can be good.
    # However, some environments might not have access during build/initial startup tests.
    logger.info("Application startup complete.")


app.include_router(locations.router, prefix="/api/v1", tags=["Locations"])
app.include_router(filters.router, prefix="/api/v1", tags=["Filters"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
