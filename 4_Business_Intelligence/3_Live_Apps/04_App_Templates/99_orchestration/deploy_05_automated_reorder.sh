#!/bin/bash
# Independent Deployment: Automated Reorder

echo "🤖 Deploying: Automated Reorder Engine"
echo ""
echo "Target: Databricks Apps (PAID tier required)"
echo ""

cd ../05_automated_reorder

# Check tier
echo "⚠️  Checking workspace tier..."
echo ""
echo "This requires Databricks Apps (paid tier feature)"
echo "Verify: Workspace Settings → Subscriptions"
echo ""

read -p "Workspace supports Databricks Apps? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "✅ Proceeding with deployment..."
    echo ""
    echo "📦 Deploying app:"
    echo "   databricks apps deploy inventory_reorder \\"
    echo "     /Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/2_Databricks_Apps/05_automated_reorder"
    echo ""
    echo "⏱️  Deployment takes ~2 minutes"
else
    echo ""
    echo "❌ Cannot deploy without paid tier"
    echo ""
    echo "Alternatives while on free tier:"
    echo "  • Use 01_realtime_monitoring for manual ordering"
    echo "  • Use 02_predictive_analytics for planning"
    echo "  • Export recommendations and process manually"
fi
