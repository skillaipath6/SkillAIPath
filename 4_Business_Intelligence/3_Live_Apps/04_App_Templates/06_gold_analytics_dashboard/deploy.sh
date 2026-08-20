#!/bin/bash
# BharatMart - Gold Analytics Dashboard Deployment Script
# Deploy Databricks App with app.yaml

set -e

echo "======================================"
echo "Deploying Gold Analytics Dashboard"
echo "======================================"

# Configuration
APP_NAME="bharatmart-gold-analytics"

echo "Deploying Databricks App..."
databricks apps deploy $APP_NAME \
    --source-code-path "$(pwd)"

echo "Starting app..."
databricks apps start $APP_NAME

echo "Getting app status..."
databricks apps get $APP_NAME

echo "✅ Gold Analytics Dashboard deployed successfully!"
echo "Access the app URL shown above"
echo "======================================"
