#!/bin/bash

# Script to create a Google Cloud Storage bucket.

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if GCS_BUCKET_NAME is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <gcs-bucket-name>"
  echo "Please provide the desired GCS bucket name as an argument."
  exit 1
fi

GCS_BUCKET_NAME=$1
PROJECT_ID=$(gcloud config get-value project)
LOCATION="US-CENTRAL1" # You can change this to your preferred location

echo "Creating GCS bucket: gs://${GCS_BUCKET_NAME} in project ${PROJECT_ID} and location ${LOCATION}..."

# Create the bucket with Uniform Bucket-Level Access
gcloud storage buckets create "gs://${GCS_BUCKET_NAME}"   --project="${PROJECT_ID}"   --location="${LOCATION}"   --uniform-bucket-level-access

echo "Bucket gs://${GCS_BUCKET_NAME} created successfully."
echo "Remember to grant necessary IAM permissions to your service account if it needs to access this bucket."
