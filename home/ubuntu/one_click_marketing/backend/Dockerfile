# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for some Python packages (if any)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Ensure gunicorn is in requirements.txt or install it separately
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy the rest of the backend application code into the container at /app
COPY . .

# Make port 8080 available to the world outside this container
# Google Cloud Run expects the container to listen on the port defined by the PORT environment variable, defaulting to 8080.
EXPOSE 8080

# Define environment variable for the PORT
ENV PORT 8080

# Run app.py when the container launches using Gunicorn
# The command should be adjusted if your main Flask app file is named differently or located elsewhere.
# Ensure src.main:app points to the correct Flask app instance.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 src.main:app
