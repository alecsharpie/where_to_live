# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 8080 available to the world outside this container
# Cloud Run expects the container to listen on the port defined by the PORT env var (defaults to 8080)
EXPOSE 8080

# Define environment variable for the Flask app (run.py without .py)
ENV FLASK_APP=run
# Define environment variable for Flask environment
ENV FLASK_ENV=production
# Define environment variable for the port (Cloud Run will set this)
ENV PORT=8080

# Run the application using gunicorn for production
# Gunicorn is a WSGI HTTP server. Add it to requirements.txt
# The command uses the PORT environment variable set by Cloud Run.
CMD exec gunicorn --bind :${PORT} --workers 1 --threads 8 --timeout 0 "app:create_app()"
