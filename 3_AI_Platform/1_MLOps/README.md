# MLOps Pipeline Guide
**10 Production Files** | **Training → Deployment → Serving** | **FREE Edition Compatible**

## 📌 Overview

Complete MLOps pipeline for retail/ecommerce ML models with FREE Databricks edition.

**Models:** Churn prediction, product recommendation, demand forecasting, next purchase  
**Deployment:** REST API endpoints, batch vs real-time, A/B testing  
**Tech:** MLflow, Feature Store, Model Serving, Unity Catalog

## 🏗 Pipeline Files

### Training Notebooks (4 files)
- 01_Churn_Prediction_Training.py
- 02_Product_Recommendation_Training.py
- 03_Demand_Forecasting_Training.py
- 04_Next_Purchase_Prediction_Training.py

**Pattern:** Train → Log to MLflow → Register to Unity Catalog

### Deployment & Serving (4 files)
- 10_Deploy_Model_Endpoint.py - Create serving endpoint
- 11_REST_API_Inference.py - Real-time inference
- 12_Batch_vs_Realtime_Comparison.py - Pattern comparison
- 13_AB_Testing_Traffic_Split.py - A/B testing setup

### Documentation (2 files)
- EXECUTIVE_SUMMARY.py - Business overview
- FREE_EDITION_MLOps_Guide.py - Implementation guide

## 🎯 Quick Start

### 1. Train Model
```python
dbutils.notebook.run("01_Churn_Prediction_Training", 1800)
```

### 2. Deploy Endpoint
```python
dbutils.notebook.run("10_Deploy_Model_Endpoint", 600)
```

### 3. Real-Time Inference
```python
dbutils.notebook.run("11_REST_API_Inference", 300)
```

## 💡 Key Features

**FREE Edition Optimized:** No premium features, Unity Catalog registry, Serverless endpoints

**Production Ready:** Model versioning, A/B testing, Batch/real-time serving, Performance monitoring

## 📊 Models

- Churn Prediction: Identify at-risk customers
- Product Recommendation: Personalized suggestions
- Demand Forecasting: Inventory planning
- Next Purchase: Customer journey prediction

## 🚀 Deployment

**Via Orchestrator:**
```python
dbutils.notebook.run("1_Canvas/2_Orchestration/AI_Platform/2_MLOps", 3600)
```

## 📚 Related

- RAG Pipeline: `../2_Rag_Pipeline/`
- AI Agents: `../3_AI_Agents/`
- Quality Ops: `../../2_Data_Production/04_Quality_Operations/`

✨ **10 files, production MLOps on FREE edition!**
