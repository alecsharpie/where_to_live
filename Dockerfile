# Stage 1: Build stage for uv (if needed, or use a base image with uv pre-installed)
# For simplicity, we'll install uv in the final stage.
# Using a specific Python version is good practice.
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
# Refer to official uv installation methods for the most up-to-date command
# Using pip to install uv as per common practice for Python tools
ENV UV_VERSION=0.1.29
RUN pip install --no-cache-dir uv==${UV_VERSION}

# Copy project dependency definition
COPY pyproject.toml ./

# Install dependencies using uv
# --system flag installs them into the system Python environment of the container
# --no-cache is good for keeping image size down
RUN uv pip sync --system --no-cache pyproject.toml

# Copy the application code into the container
COPY ./app ./app

# Environment variables that the application expects.
# These should be provided during 'docker run' or by the cloud environment.
# Default values are provided here for documentation purposes only;
# they might not be functional without actual values.
ENV GCS_BUCKET_NAME="your-gcs-bucket-name"
ENV GCS_DATA_BLOB_NAME="locations.json"
ENV GOOGLE_MAPS_API_KEY_SECRET_NAME="projects/your-gcp-project-id/secrets/your-secret-name/versions/latest"
ENV GCP_PROJECT_ID="your-gcp-project-id"
# Uvicorn specific
ENV HOST="0.0.0.0"
ENV PORT="8000"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Use the full path to uv if it's not in PATH or use 'python -m uvicorn'
# Using 'uvicorn' directly as uv should add it to the path when installed via 'uv pip sync --system'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
