#!/bin/bash
# BharatMart - Executive Reporting Deployment Script
# Deploy Lakeview Dashboard datasets

set -e

echo "======================================"
echo "Deploying Executive Reporting Dashboard"
echo "======================================"

# Configuration
CATALOG="bharatmart_catalog"
SCHEMA="bharatmart_silver"

echo "Creating Unity Catalog datasets..."

# Create or refresh datasets
for sql_file in dataset_*.sql; do
    echo "Processing $sql_file..."
    databricks sql execute \
        --file "$sql_file" \
        --warehouse-id "$DATABRICKS_WAREHOUSE_ID"
done

echo "✅ Executive Reporting datasets deployed successfully!"
echo "Next: Import into Lakeview Dashboard"
echo "======================================"
