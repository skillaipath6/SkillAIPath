#!/bin/bash
# BharatMart - Supply Chain API Deployment Script
# Deploy production-grade REST API with authentication

set -e

echo "======================================"
echo "Deploying Supply Chain API"
echo "======================================"

# Configuration
APP_NAME="bharatmart-supply-chain-api"
APP_DIR="04_supply_chain_api"
DOCKER_IMAGE="bharatmart/supply-chain-api:latest"

# Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }

# Build Docker image
echo "Building Docker image..."
cd $APP_DIR
docker build -t $DOCKER_IMAGE .

# Run application
echo "Starting API..."
docker run -d \
    --name $APP_NAME \
    -p 5000:5000 \
    -e DATABRICKS_SERVER_HOSTNAME="$DATABRICKS_SERVER_HOSTNAME" \
    -e DATABRICKS_HTTP_PATH="$DATABRICKS_HTTP_PATH" \
    -e DATABRICKS_TOKEN="$DATABRICKS_TOKEN" \
    -e API_TOKENS="$API_TOKENS" \
    -e ENVIRONMENT="production" \
    $DOCKER_IMAGE

# Health check
echo "Performing health check..."
sleep 5
curl -f http://localhost:5000/health || { echo "Health check failed. Check logs."; exit 1; }

echo "✅ Supply Chain API deployed successfully!"
echo "API endpoint: http://localhost:5000"
echo "Health check: http://localhost:5000/health"
echo "API docs: http://localhost:5000/"
echo "======================================"
