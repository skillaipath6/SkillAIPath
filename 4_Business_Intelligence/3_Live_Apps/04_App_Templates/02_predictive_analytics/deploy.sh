#!/bin/bash
# BharatMart - Predictive Analytics Deployment Script
# Deploy Prophet ML forecasting application

set -e

echo "======================================"
echo "Deploying Predictive Analytics App"
echo "======================================"

# Configuration
APP_NAME="bharatmart-predictive-analytics"
APP_DIR="02_predictive_analytics"
DOCKER_IMAGE="bharatmart/predictive-analytics:latest"

# Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }

# Build Docker image
echo "Building Docker image..."
cd $APP_DIR
docker build -t $DOCKER_IMAGE .

# Run application
echo "Starting application..."
docker run -d \
    --name $APP_NAME \
    -p 8502:8501 \
    -e DATABRICKS_SERVER_HOSTNAME="$DATABRICKS_SERVER_HOSTNAME" \
    -e DATABRICKS_HTTP_PATH="$DATABRICKS_HTTP_PATH" \
    -e DATABRICKS_TOKEN="$DATABRICKS_TOKEN" \
    $DOCKER_IMAGE

echo "✅ Predictive Analytics deployed successfully!"
echo "Access at: http://localhost:8502"
echo "======================================"
