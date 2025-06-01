#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Variables - PLEASE UPDATE THESE BEFORE RUNNING
PROJECT_ID="where-to-live-nz" # Replace with your GCP Project ID if different
CLOUD_SQL_INSTANCE_NAME="wtl-nz-db-pg" # Choose a name for your Cloud SQL instance
DB_USER="wtl_user" # Choose a username for the database
# IMPORTANT: Choose a strong password for the database user
DB_PASSWORD="your-strong-password-here" # REPLACE THIS WITH A STRONG PASSWORD
REGION="australia-southeast1" # Choose the region for your Cloud SQL instance
SERVICE_ACCOUNT_NAME="wtl-nz-app-sa" # Choose a name for your service account
SERVICE_ACCOUNT_DISPLAY_NAME="Where To Live NZ App Service Account"

echo "Starting GCP resource setup for project: $PROJECT_ID"

# Enable necessary APIs
echo "Enabling APIs: SQL Admin, IAM, and Google Maps APIs (if not already enabled)..."
gcloud services enable sqladmin.googleapis.com     iam.googleapis.com     routespreferred.googleapis.com     places.googleapis.com     geocoding.googleapis.com     --project="$PROJECT_ID"

echo "APIs enabled."

# Create Cloud SQL for PostgreSQL instance
echo "Creating Cloud SQL for PostgreSQL instance: $CLOUD_SQL_INSTANCE_NAME in region $REGION..."
gcloud sql instances create "$CLOUD_SQL_INSTANCE_NAME"     --database-version=POSTGRES_15     --tier=db-f1-micro     --region="$REGION"     --project="$PROJECT_ID"     --database-flags=cloudsql.iam_authentication=On # Enable IAM authentication

echo "Cloud SQL instance created."
echo "IMPORTANT: Note down the instance connection name. It will be something like '$PROJECT_ID:$REGION:$CLOUD_SQL_INSTANCE_NAME'"

# Set the root password for the PostgreSQL instance (optional, IAM auth is preferred)
# echo "Setting root password for $CLOUD_SQL_INSTANCE_NAME..."
# gcloud sql users set-password postgres #     --instance="$CLOUD_SQL_INSTANCE_NAME" #     --prompt-for-password #     --project="$PROJECT_ID"

# Create a database user
echo "Creating database user '$DB_USER' for instance '$CLOUD_SQL_INSTANCE_NAME'..."
gcloud sql users create "$DB_USER"     --instance="$CLOUD_SQL_INSTANCE_NAME"     --password="$DB_PASSWORD"     --project="$PROJECT_ID"

echo "Database user '$DB_USER' created."
echo "IMPORTANT: Remember the password you set for $DB_USER: $DB_PASSWORD"

# Create a dedicated database (optional, can be done via psql later)
# DB_NAME="wtl_database"
# echo "Creating database '$DB_NAME' in instance '$CLOUD_SQL_INSTANCE_NAME'..."
# gcloud sql databases create "$DB_NAME" #     --instance="$CLOUD_SQL_INSTANCE_NAME" #     --project="$PROJECT_ID"
# echo "Database '$DB_NAME' created."

# Create a service account
echo "Creating service account: $SERVICE_ACCOUNT_NAME..."
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME"     --description="$SERVICE_ACCOUNT_DISPLAY_NAME"     --display-name="$SERVICE_ACCOUNT_DISPLAY_NAME"     --project="$PROJECT_ID"

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Service account $SERVICE_ACCOUNT_EMAIL created."

# Grant permissions to the service account
echo "Granting permissions to service account $SERVICE_ACCOUNT_EMAIL..."

# Cloud SQL Client (to connect to the database)
gcloud projects add-iam-policy-binding "$PROJECT_ID"     --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL"     --role="roles/cloudsql.client"

# Roles for Google Maps APIs (adjust if needed, e.g., if you only need specific APIs)
# This grants broader access; for production, consider more granular permissions.
gcloud projects add-iam-policy-binding "$PROJECT_ID"     --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL"     --role="roles/routespreferred.user" # For Directions API

gcloud projects add-iam-policy-binding "$PROJECT_ID"     --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL"     --role="roles/places.user" # For Places API

gcloud projects add-iam-policy-binding "$PROJECT_ID"     --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL"     --role="roles/geocoding.user" # For Geocoding API


# If you plan to run the app on Cloud Run or App Engine, you might also need:
# roles/run.invoker (for Cloud Run)
# roles/appengine.appViewer and roles/iap.securedAppUser (for App Engine with IAP)

echo "Permissions granted."

# (Optional) Create and download a key for the service account
# This is generally not recommended for applications running on GCP,
# as they can use the metadata server to get credentials.
# However, it can be useful for local development if not using `gcloud auth application-default login`.
# mkdir -p ./secrets
# echo "Creating and downloading key for service account $SERVICE_ACCOUNT_EMAIL into ./secrets/ ..."
# gcloud iam service-accounts keys create "./secrets/${SERVICE_ACCOUNT_NAME}-key.json" #     --iam-account="$SERVICE_ACCOUNT_EMAIL" #     --project="$PROJECT_ID"
# echo "Service account key downloaded to ./secrets/${SERVICE_ACCOUNT_NAME}-key.json"
# echo "IMPORTANT: Secure this key file and add it to your .gitignore if you haven't already!"

echo "GCP resource setup script created at gcp-setup/setup_gcp.sh"
echo "------------------------------------------------------------------"
echo "IMPORTANT NEXT STEPS:"
echo "1. REVIEW AND UPDATE the variables at the top of 'gcp-setup/setup_gcp.sh' (especially PROJECT_ID and DB_PASSWORD)."
echo "2. MAKE THE SCRIPT EXECUTABLE: chmod +x gcp-setup/setup_gcp.sh"
echo "3. RUN THE SCRIPT from your terminal: ./gcp-setup/setup_gcp.sh"
echo "4. SECURELY STORE the DB_PASSWORD and any generated service account keys."
echo "5. ADD 'secrets/' directory and '*.json' (if you generate keys) to your .gitignore file."
echo "------------------------------------------------------------------"
