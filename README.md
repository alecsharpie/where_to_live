# Where To Live NZ - Backend API

This project provides the backend API for a tool to help decide where to move in New Zealand. It allows managing a list of potential locations, storing their data, and filtering them based on driving time from a specified address.

The backend is built using Python with the FastAPI framework and is designed to be deployed using Docker on the Google Cloud Platform (GCP).

## Features

*   **Location Management:** CRUD (Create, Read, Update, Delete) operations for potential residential locations.
*   **Data Storage:** Location data is stored as a JSON file in a Google Cloud Storage (GCS) bucket.
*   **Driving Time Filter:** Filter locations based on maximum driving time from a user-provided source address, utilizing Google Maps APIs.
*   **Secure API Key Management:** Google Maps API key is managed via Google Secret Manager.
*   **Containerized:** Dockerfile provided for easy deployment and consistent environments.
*   **Scalable Design:** Data models and fetching logic are designed with future data enrichment in mind (e.g., population, local amenities).

## Tech Stack

*   Python 3.11+
*   FastAPI: For building the REST API.
*   Uvicorn: ASGI server for FastAPI.
*   Pydantic: For data validation and settings management.
*   Google Cloud Storage (GCS): For data persistence.
*   Google Secret Manager: For API key storage.
*   Google Maps APIs: (Geocoding, Distance Matrix) for location services.
*   uv: For Python packaging and project management.
*   Docker: For containerization.

---

# Helping my wife and I decide where to live when we move back to New Zealand

## Project Setup

### Prerequisites

*   Google Cloud SDK (`gcloud`) installed and authenticated.
*   Python (latest stable version recommended) with \`uv\` installed.
*   Docker (for containerization).

### Initial GCP Setup

1.  **Login to gcloud:**
    \`\`\`bash
    gcloud auth login
    gcloud config set project where-to-live-nz # Replace with your GCP Project ID if different
    \`\`\`

2.  **Create GCS Bucket:**
    A Google Cloud Storage bucket is needed to store the locations data (e.g., \`locations.json\`).
    \`\`\`bash
    ./scripts/setup_gcs.sh your-chosen-bucket-name
    \`\`\`
    Replace \`your-chosen-bucket-name\` with a unique name for your bucket.

3.  **Store Google Maps API Key in Secret Manager:**
    A Google Maps API key is required for geocoding and distance calculations. Ensure you have an API key with "Maps JavaScript API", "Geocoding API", and "Distance Matrix API" enabled.
    \`\`\`bash
    ./scripts/setup_secrets.sh google-maps-api-key YOUR_GOOGLE_MAPS_API_KEY_VALUE
    \`\`\`
    Replace \`YOUR_GOOGLE_MAPS_API_KEY_VALUE\` with your actual Google Maps API key.
    This will create a secret named \`google-maps-api-key\`.

    You will need to grant your application's service account (e.g., the one used by Cloud Run or GCE) permission to access this secret. The script will output a sample command for this.

### Local Development Setup

1.  **Clone the repository:**
    \`\`\`bash
    # git clone ... (assuming you've done this)
    cd where-to-live-nz
    \`\`\`

2.  **Install Python Dependencies:**
    This project uses \`uv\` for package management.
    \`\`\`bash
    uv pip sync pyproject.toml
    \`\`\`

3.  **Configure Environment Variables:**
    Create a \`.env\` file in the root of the project by copying \`.env.example\` (which will be created in a later step) and filling in the values.
    \`\`\`
    # .env (example content - will be formally defined later)
    GCP_PROJECT_ID="where-to-live-nz"
    GCS_BUCKET_NAME="your-chosen-bucket-name"
    GCS_DATA_BLOB_NAME="locations.json"
    GOOGLE_MAPS_API_KEY_SECRET_NAME="projects/where-to-live-nz/secrets/google-maps-api-key/versions/latest"
    \`\`\`

---

### Environment Variable Configuration

Create a \`.env\` file in the project root (not the \`app\` directory, for \`python-dotenv\` to pick it up easily when running \`uvicorn\` from the root) by copying \`app/.env.example\` and filling in your actual values.

\`\`\`bash
cp app/.env.example .env
\`\`\`

Then edit the \`.env\` file with your specific configuration:

\`\`\`env
# .env - Fill these values
GCP_PROJECT_ID="your-gcp-project-id"
GCS_BUCKET_NAME="your-unique-gcs-bucket-name" # Must match the one created with setup_gcs.sh
GCS_DATA_BLOB_NAME="locations.json" # Or your chosen blob name
GOOGLE_MAPS_API_KEY_SECRET_NAME="projects/your-gcp-project-id/secrets/google-maps-api-key/versions/latest" # Ensure 'google-maps-api-key' matches the name used in setup_secrets.sh
# HOST="127.0.0.1" # Optional for local uvicorn run
# PORT="8000"      # Optional for local uvicorn run
\`\`\`
**Important:** The \`.env\` file is gitignored and should never be committed to your repository.

### Running the Application Locally

Once dependencies are installed and your \`.env\` file is configured:

\`\`\`bash
uvicorn app.main:app --reload --host \$(grep -E '^HOST=' .env | cut -d '=' -f2 || echo "127.0.0.1") --port \$(grep -E '^PORT=' .env | cut -d '=' -f2 || echo "8000")
\`\`\`
Or more simply if you rely on default host/port or have them set in \`.env\` and your \`app.main\` doesn't override them:
\`\`\`bash
uvicorn app.main:app --reload
\`\`\`
The API will typically be available at \`http://127.0.0.1:8000\`. You can access the OpenAPI documentation at \`http://127.0.0.1:8000/docs\`.

### Building and Running with Docker

1.  **Build the Docker Image:**
    From the project root directory:
    \`\`\`bash
    docker build -t where-to-live-nz-api .
    \`\`\`

2.  **Run the Docker Container:**
    You need to pass the environment variables to the container. You can do this using an \`env-file\` or individual \`-e\` flags.
    Using an env-file (recommended for multiple variables):
    Ensure your \`.env\` file (created above) has the correct values.
    \`\`\`bash
    docker run -d -p 8000:8000 --env-file ./.env where-to-live-nz-api
    \`\`\`
    Or using individual \`-e\` flags:
    \`\`\`bash
    docker run -d -p 8000:8000 \
      -e GCP_PROJECT_ID="your-gcp-project-id" \
      -e GCS_BUCKET_NAME="your-gcs-bucket-name" \
      -e GCS_DATA_BLOB_NAME="locations.json" \
      -e GOOGLE_MAPS_API_KEY_SECRET_NAME="projects/your-gcp-project-id/secrets/google-maps-api-key/versions/latest" \
      where-to-live-nz-api
    \`\`\`
    The API will then be accessible at \`http://localhost:8000\`, and docs at \`http://localhost:8000/docs\`.

## API Endpoints Overview

The API is prefixed with \`/api/v1\`.

### Health Check

*   **GET \`/health\`**: Returns the operational status of the API.

### Locations

*   **POST \`/locations\`**: Create a new location.
    *   Request Body: \`LocationCreate\` model (name, address, notes, optional lat/lng).
*   **GET \`/locations\`**: Retrieve a list of all stored locations.
*   **GET \`/locations/{location_id}\`**: Retrieve a specific location by its ID.
*   **PUT \`/locations/{location_id}\`**: Update an existing location.
    *   Request Body: \`LocationUpdate\` model (optional fields for name, address, notes, lat/lng, enrichment_data).
*   **DELETE \`/locations/{location_id}\`**: Delete a location by its ID.

### Filters

*   **POST \`/filter_by_driving_time\`**: Filter locations by driving time.
    *   Request Body:
        \`\`\`json
        {
          "source_address": "Your Starting Address, City, NZ",
          "max_driving_time_minutes": 60
        }
        \`\`\`
    *   Response: A list of \`LocationModel\` objects that are within the specified driving time, including the calculated \`driving_time_to_target_seconds\`. Locations that cannot be geocoded or for which a route cannot be found will be omitted.

## Future Scalability & Data Enrichment

The \`LocationModel\` includes an \`enrichment_data: Optional[Dict]\` field. This is a placeholder for future enhancements where additional, potentially unstructured, data can be added to each location. Examples include:

*   Population statistics.
*   Links to Wikipedia pages or local council websites.
*   Information about local amenities (schools, parks, supermarkets).
*   Property market data.

This data could be gathered via:
*   Additional API integrations.
*   Web scraping (responsibly).
*   Manual input through an admin interface (to be built in a future phase).
*   AI agents for information gathering and summarization.

The current design of storing data in GCS as JSON blobs is flexible enough to accommodate these additions. For more complex querying or relational data, transitioning to a database like PostgreSQL or Cloud SQL might be considered in the future.

## Contributing

Contributions are welcome! Please fork the repository, create a new branch for your feature or fix, and submit a pull request.
