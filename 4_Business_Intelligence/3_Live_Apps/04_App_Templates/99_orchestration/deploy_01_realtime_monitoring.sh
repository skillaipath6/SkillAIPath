#!/bin/bash
# Independent Deployment: Real-Time Monitoring

echo "🚨 Deploying: Real-Time Monitoring Dashboard"
echo ""
echo "Target: Streamlit Cloud (FREE)"
echo ""

cd ../01_realtime_monitoring

# Check prerequisites
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

echo "📋 Deployment Steps:"
echo "1. Push to GitHub:"
echo "   git add 01_realtime_monitoring/"
echo "   git commit -m \"Deploy real-time monitoring\""
echo "   git push"
echo ""
echo "2. Deploy to Streamlit Cloud:"
echo "   • Visit: https://share.streamlit.io"
echo "   • Select repository"
echo "   • Main file: 01_realtime_monitoring/app.py"
echo "   • Add secrets (Databricks credentials)"
echo ""
echo "3. Access your live dashboard"
echo ""

# Test locally
echo "🧪 Test locally first:"
echo "   pip install -r requirements.txt"
echo "   streamlit run app.py"
echo ""

echo "✅ Deployment guide complete"
