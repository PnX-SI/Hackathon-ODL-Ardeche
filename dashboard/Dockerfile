# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /

# Install system dependencies for GeoPandas
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8051

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "dashboard.py"]
