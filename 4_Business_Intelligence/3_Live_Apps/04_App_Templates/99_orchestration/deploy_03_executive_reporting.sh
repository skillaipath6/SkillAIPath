#!/bin/bash
# Independent Deployment: Executive Reporting

echo "📊 Deploying: Executive Reporting Dashboard"
echo ""
echo "Target: Databricks Lakeview (FREE)"
echo ""

cd ../03_executive_reporting

echo "📋 Deployment Steps:"
echo ""
echo "1. Open Databricks Workspace → Dashboards"
echo "2. Create new dashboard: \"BharatMart Executive Metrics\""
echo "3. Import SQL files:"
ls -1 *.sql 2>/dev/null | while read file; do
    echo "   • $file"
done
echo ""
echo "4. Add widgets:"
echo "   • Counters for KPIs"
echo "   • Line charts for trends"
echo "   • Tables for details"
echo ""
echo "5. Schedule refresh: Hourly"
echo "6. Share with C-suite"
echo ""

echo "✅ SQL datasets ready for import"
