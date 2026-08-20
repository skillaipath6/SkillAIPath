#!/bin/bash
# Independent Deployment: Supply Chain API

echo "🔌 Deploying: Supply Chain Integration API"
echo ""
echo "Target: Docker → Cloud (AWS/GCP/Azure)"
echo ""

cd ../04_supply_chain_api

echo "🐳 Docker Deployment:"
echo ""
echo "1. Build image:"
echo "   docker build -t bharatmart-api ."
echo ""
echo "2. Test locally:"
echo "   docker run -p 5000:5000 --env-file .env bharatmart-api"
echo "   curl http://localhost:5000"
echo ""
echo "3. Deploy to cloud:"
echo ""
echo "   AWS (ECS/Lambda):"
echo "     aws ecr create-repository --repository-name bharatmart-api"
echo "     docker tag bharatmart-api:latest <aws-account>.dkr.ecr.region.amazonaws.com/bharatmart-api"
echo "     docker push <aws-account>.dkr.ecr.region.amazonaws.com/bharatmart-api"
echo ""
echo "   GCP (Cloud Run):"
echo "     gcloud run deploy bharatmart-api --image bharatmart-api --platform managed"
echo ""
echo "   Azure (Container Apps):"
echo "     az containerapp up --name bharatmart-api --source ."
echo ""

echo "✅ API endpoints ready for integration"
