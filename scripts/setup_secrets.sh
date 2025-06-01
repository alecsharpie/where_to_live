#!/bin/bash

# Script to create a secret in Google Secret Manager.

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if SECRET_NAME and SECRET_VALUE are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <secret-name> <secret-value>"
  echo "Please provide the desired secret name (e.g., google-maps-api-key) and its value as arguments."
  exit 1
fi

SECRET_NAME=$1
SECRET_VALUE=$2
PROJECT_ID=$(gcloud config get-value project)

echo "Creating secret: ${SECRET_NAME} in project ${PROJECT_ID}..."

# Create the secret
gcloud secrets create "${SECRET_NAME}"   --project="${PROJECT_ID}"   --replication-policy="automatic"

# Add the secret version
echo -n "${SECRET_VALUE}" | gcloud secrets versions add "${SECRET_NAME}"   --project="${PROJECT_ID}"   --data-file=-

echo "Secret ${SECRET_NAME} created and version added successfully."
echo "To grant access to this secret, use a command like:"
echo "gcloud secrets add-iam-policy-binding ${SECRET_NAME} --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" --role="roles/secretmanager.secretAccessor" --project="${PROJECT_ID}""
