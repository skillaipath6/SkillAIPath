#!/bin/bash
# BharatMart - Automated Reorder Deployment Script
# Deploy Databricks App with app.yaml

set -e

echo "======================================"
echo "Deploying Automated Reorder App"
echo "======================================"

# Configuration
APP_NAME="bharatmart-automated-reorder"

echo "Deploying Databricks App..."
databricks apps deploy $APP_NAME \
    --source-code-path "$(pwd)"

echo "Starting app..."
databricks apps start $APP_NAME

echo "Getting app status..."
databricks apps get $APP_NAME

echo "✅ Automated Reorder App deployed successfully!"
echo "======================================"
