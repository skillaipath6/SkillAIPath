#!/bin/bash
# Independent Deployment: Predictive Analytics

echo "📈 Deploying: Predictive Analytics Engine"
echo ""
echo "Target: Streamlit Cloud or Docker (FREE)"
echo ""

cd ../02_predictive_analytics

echo "Option 1: Streamlit Cloud (Recommended)"
echo "  Same as 01_realtime_monitoring"
echo ""

echo "Option 2: Docker Deployment"
echo "  docker build -t bharatmart-forecasting ."
echo "  docker run -p 8501:8501 --env-file .env bharatmart-forecasting"
echo ""

echo "✅ ML models included: Facebook Prophet"
echo "✅ Forecasts: 30-180 days ahead"
