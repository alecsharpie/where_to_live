# Where To Live NZ

This project is a web application to help users decide where to move in New Zealand based on various criteria, starting with proximity to a specified address.

## Project Overview

The application will feature:
- A map of New Zealand.
- Filtering of locations based on driving time from a user-provided address.
- Data fetched from Google Maps/Places APIs.
- Scalable data storage for location information.
- An admin tool for managing the location dataset.

## Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML, CSS, JavaScript (with Leaflet.js for mapping)
- **Database:** PostgreSQL (on Google Cloud SQL)
- **Platform:** Google Cloud Platform (GCP)

## Setup and Running the Project

### Prerequisites

- Python 3.x
- pip (Python package installer)
- Google Cloud SDK (`gcloud` CLI) (for GCP integration, if applicable)

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd where-to-live-nz
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set Google Maps API Key:**
    The application requires a Google Maps API key with the following APIs enabled:
    - Directions API
    - Geocoding API
    - Places API

    Set the API key as an environment variable:
    ```bash
    export GOOGLE_MAPS_API_KEY="YOUR_API_KEY"
    ```
    Replace `"YOUR_API_KEY"` with your actual key. For production, manage this key securely (e.g., using GCP Secret Manager and exposing it as an environment variable to your Cloud Run/App Engine service).

5.  **Database Configuration:**
    The application uses Flask-SQLAlchemy for database interactions.
    - For **local development**, it defaults to using an SQLite database file (`local_dev.db`) created in the project root.
    - To use **PostgreSQL (e.g., on Google Cloud SQL)**, set the `DATABASE_URI` environment variable.
      The format for Cloud SQL (using IAM authentication with the Cloud SQL Proxy) is:
      ```
      export DATABASE_URI="postgresql+psycopg2://<DB_USER>@/<DB_NAME>?host=/cloudsql/<PROJECT_ID>:<REGION>:<INSTANCE_NAME>"
      ```
      Replace `<DB_USER>`, `<DB_NAME>`, `<PROJECT_ID>`, `<REGION>`, and `<INSTANCE_NAME>` with your actual values.
      Example:
      ```
      export DATABASE_URI="postgresql+psycopg2://wtl_user@wtl_database?host=/cloudsql/where-to-live-nz:australia-southeast1:wtl-nz-db-pg"
      ```
      You would also need to:
        - Ensure the `psycopg2-binary` package is installed (it's in `requirements.txt`).
        - Have the Cloud SQL Auth Proxy running and configured for your instance.
        - Create the database (e.g., `wtl_database`) within your Cloud SQL instance if you haven't already via the `gcp-setup/setup_gcp.sh` script or manually.
        - Ensure the database user has permissions to this database.

6.  **Run the Flask development server:**
    ```bash
    python run.py
    ```
    The backend will be accessible at `http://127.0.0.1:5000`. You can check the health endpoint at `http://127.0.0.1:5000/api/health`.

### Frontend Setup

(Instructions will be added once the frontend is developed)

### GCP Setup

(Instructions for setting up necessary GCP resources like Cloud SQL and service accounts will be added here. See `gcp-setup/` directory for scripts once available.)

## Deployment

This application is designed to be deployed as a container, for example, on Google Cloud Run.

### Prerequisites for Deployment

- Docker installed locally.
- Google Cloud SDK (`gcloud`) configured and authenticated with your GCP project.
- A Google Cloud Project with the following:
    - Cloud Run API enabled.
    - Artifact Registry API enabled (or Container Registry).
    - A configured Cloud SQL for PostgreSQL instance (see `gcp-setup/setup_gcp.sh`).
    - The service account created by `gcp-setup/setup_gcp.sh` (or a similar one) should have:
        - Cloud SQL Client role (to connect to the database).
        - Roles for Google Maps APIs (e.g., `roles/routespreferred.user`, `roles/places.user`, `roles/geocoding.user`).
        - Secret Manager Secret Accessor role (if using Secret Manager for API keys).

### 1. Build the Docker Image

Navigate to the project root directory (where the `Dockerfile` is located) and run:
```bash
# Replace <YOUR_PROJECT_ID> and <YOUR_IMAGE_NAME>
export PROJECT_ID="where-to-live-nz" # Or your GCP project ID
export IMAGE_NAME="wtl-nz-app"
export IMAGE_TAG="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest" # For Google Container Registry
# Or for Artifact Registry:
# export AR_REGION="australia-southeast1" # e.g., your Artifact Registry region
# export AR_REPO_NAME="my-app-repo" # Your Artifact Registry repo name
# export IMAGE_TAG="${AR_REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO_NAME}/${IMAGE_NAME}:latest"

docker build -t "${IMAGE_TAG}" .
```

### 2. Push the Image to a Registry

**For Google Container Registry (GCR):**
```bash
docker push "${IMAGE_TAG}"
```
*(Note: GCR is being superseded by Artifact Registry. New projects should prefer Artifact Registry.)*

**For Artifact Registry:**
Ensure you have created a Docker repository in Artifact Registry.
```bash
# Example: gcloud artifacts repositories create my-app-repo --repository-format=docker --location=australia-southeast1 --description="Docker repository for WTL NZ app"
docker push "${IMAGE_TAG}"
```

### 3. Deploy to Google Cloud Run

Replace placeholders accordingly.

```bash
SERVICE_NAME="where-to-live-nz" # Choose a name for your Cloud Run service
REGION="australia-southeast1"    # The region for your Cloud Run service

# Environment variables:
# **IMPORTANT**: For production, store sensitive values like GOOGLE_MAPS_API_KEY and
# the database password in Secret Manager and grant the Cloud Run service's
# runtime service account access to these secrets. Then, mount them as environment variables.

# Example for direct environment variables (less secure for secrets):
# export GOOGLE_MAPS_API_KEY_VALUE="your_actual_google_maps_api_key"
# export DB_USER_VALUE="wtl_user"
# export DB_PASSWORD_VALUE="your_db_password" # VERY INSECURE
# export DB_NAME_VALUE="wtl_database"
# export CLOUD_SQL_CONNECTION_NAME_VALUE="<YOUR_PROJECT_ID>:<YOUR_SQL_REGION>:<YOUR_SQL_INSTANCE_NAME>"
# Example: "where-to-live-nz:australia-southeast1:wtl-nz-db-pg"

# Recommended: Using Secret Manager (replace with your secret versions)
# Create secrets first, e.g.:
# echo -n "your_api_key" | gcloud secrets create GOOGLE_MAPS_API_KEY_SECRET --data-file=- --project=$PROJECT_ID
# echo -n "your_db_password" | gcloud secrets create DB_PASSWORD_SECRET --data-file=- --project=$PROJECT_ID

# Then, when deploying, reference these secrets.
# The runtime service account of Cloud Run will need "Secret Manager Secret Accessor" role.

gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_TAG}" \
    --platform=managed \
    --region="${REGION}" \
    --allow-unauthenticated \
    --add-cloudsql-instances="<YOUR_PROJECT_ID>:<YOUR_SQL_REGION>:<YOUR_SQL_INSTANCE_NAME>" \
    --set-env-vars="FLASK_ENV=production" \
    --set-env-vars="^##^DATABASE_URI=postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@/<DB_NAME>?host=/cloudsql/<YOUR_PROJECT_ID>:<YOUR_SQL_REGION>:<YOUR_SQL_INSTANCE_NAME>" \
    --set-env-vars="GOOGLE_MAPS_API_KEY=<YOUR_GOOGLE_MAPS_API_KEY>"
    # For DATABASE_URI with Secret Manager for password:
    # Example: --set-secrets="DB_PASSWORD=DB_PASSWORD_SECRET:latest"
    # And then construct DATABASE_URI in your app or entrypoint to use DB_PASSWORD,
    # or if Cloud Run supports direct substitution in --set-env-vars with secrets (check current gcloud features).
    # A common pattern is to have a placeholder in DATABASE_URI and replace it at runtime
    # from the secret-backed environment variable.
    #
    # For GOOGLE_MAPS_API_KEY from Secret Manager:
    # --set-secrets="GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY_SECRET:latest"
    # This mounts the secret value into the GOOGLE_MAPS_API_KEY env var.

echo "Make sure to replace placeholders in the gcloud run deploy command:"
echo "- <YOUR_PROJECT_ID>:<YOUR_SQL_REGION>:<YOUR_SQL_INSTANCE_NAME> (Cloud SQL connection name)"
echo "- <DB_USER>, <DB_PASSWORD>, <DB_NAME> in DATABASE_URI"
echo "- <YOUR_GOOGLE_MAPS_API_KEY> or configure Secret Manager"
echo "For DATABASE_URI, if password contains special characters, ensure it's URL encoded or use Secret Manager."
```
