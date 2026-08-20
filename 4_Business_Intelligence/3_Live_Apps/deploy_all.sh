#!/bin/bash
# Deploy all 3 apps locally

echo "🚀 Deploying SkillAIPath Live Apps"
echo "=================================="

# Check environment variables
if [ -z "$DATABRICKS_SERVER_HOSTNAME" ]; then
    echo "❌ Error: DATABRICKS_SERVER_HOSTNAME not set"
    exit 1
fi

echo "✅ Environment variables configured"

# Deploy App 1
echo ""
echo "📦 App 1: Inventory Command Center"
cd 01_Inventory_Command_Center
pip install -r requirements.txt --quiet
streamlit run app.py &
APP1_PID=$!
echo "   Running on http://localhost:8501"

# Deploy App 2
echo ""
echo "📦 App 2: Demand Forecasting Dashboard"
cd ../02_Demand_Forecasting_Dashboard
pip install -r requirements.txt --quiet
streamlit run app.py --server.port 8502 &
APP2_PID=$!
echo "   Running on http://localhost:8502"

# Deploy App 3
echo ""
echo "📦 App 3: Dynamic Pricing API"
cd ../03_Dynamic_Pricing_API
pip install -r requirements.txt --quiet
uvicorn app:app --port 8000 &
APP3_PID=$!
echo "   Running on http://localhost:8000"

echo ""
echo "=================================="
echo "✅ All apps deployed!"
echo ""
echo "🌐 Access URLs:"
echo "   App 1: http://localhost:8501"
echo "   App 2: http://localhost:8502"
echo "   App 3: http://localhost:8000"
echo ""
echo "📊 Swagger API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all apps"

# Wait for all processes
wait
