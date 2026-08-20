# App Templates Guide
**6 Production-Ready Reference Patterns** | **Flask + Streamlit + FastAPI**

## 📌 Overview

Complete app template library with production-ready patterns for common business use cases.

**Location:** `/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/04_App_Templates/`

## 🏗 Available Templates

### 1. Inventory Command Center (Streamlit)
**File:** `inventory_command_center_app.py`

**What it does:**
- Real-time inventory monitoring dashboard
- Approval workflow for reorder requests
- Audit trail with Lakebase Postgres

**Tech Stack:**
- Streamlit UI
- Unity Catalog (read analytics)
- Lakebase Postgres (write approvals)

**Use Cases:**
- Inventory management
- Approval workflows
- Real-time monitoring

---

### 2. Demand Forecasting Dashboard (Streamlit)
**File:** `demand_forecasting_dashboard.py`

**What it does:**
- ML-powered demand forecasting
- Historical sales trend analysis
- Prophet time-series models

**Tech Stack:**
- Streamlit UI
- Prophet ML library
- Unity Catalog data source
- Lakebase forecast audit

**Use Cases:**
- Demand planning
- Sales forecasting
- ML dashboards

---

### 3. Dynamic Pricing API (FastAPI)
**File:** `dynamic_pricing_api.py`

**What it does:**
- REST API for dynamic pricing
- Rule-based price adjustments
- Inventory-driven pricing logic

**Tech Stack:**
- FastAPI framework
- Unity Catalog integration
- JSON response format

**Use Cases:**
- Pricing engines
- API backends
- Dynamic pricing

---

### 4. Customer Insights Dashboard (Streamlit)
**File:** `customer_insights_dashboard.py`

**What it does:**
- Customer 360 analytics
- RFM segmentation
- Behavioral analysis

**Tech Stack:**
- Streamlit multi-page app
- Unity Catalog marts
- Interactive visualizations

**Use Cases:**
- Customer analytics
- Marketing dashboards
- Segmentation analysis

---

### 5. Real-Time Sales Monitor (Flask)
**File:** `realtime_sales_monitor.py`

**What it does:**
- Live sales KPI tracking
- Streaming data dashboard
- Alert thresholds

**Tech Stack:**
- Flask web framework
- Unity Catalog streaming tables
- WebSocket updates

**Use Cases:**
- Real-time monitoring
- Sales dashboards
- KPI tracking

---

### 6. Data Quality Dashboard (Streamlit)
**File:** `data_quality_dashboard.py`

**What it does:**
- Data quality metrics
- Validation results
- Quality gate status

**Tech Stack:**
- Streamlit UI
- Quality Operations integration
- Unity Catalog DQ tables

**Use Cases:**
- Data quality monitoring
- Validation dashboards
- Quality ops

---

## 🚀 Quick Start

### Clone Template
```python
# Copy template to your project
import shutil
shutil.copy(
    "/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/04_App_Templates/inventory_command_center_app.py",
    "/Workspace/Users/your.email@company.com/my_app.py"
)
```

### Run Locally
```bash
# Streamlit apps
streamlit run my_app.py

# FastAPI apps
uvicorn my_app:app --reload

# Flask apps
flask run
```

### Deploy to Databricks Apps
```bash
# Via CLI
databricks apps create my-app --source-code-path /Workspace/Users/your.email@company.com/my_app/

# Via UI
Apps → Create App → Upload files
```

---

## 💡 Pattern Architecture

**All templates follow:**
- Unity Catalog for analytical reads (OLAP)
- Lakebase Postgres for transactional writes (OLTP)
- Modular, reusable components
- Production-ready error handling
- Logging and monitoring

**READ from Unity Catalog:**
- `sap_dev.silver.*` (dimensions, facts)
- `sap_dev.gold.*` (marts, aggregations)

**WRITE to Lakebase:**
- `retail-ops-apps` project
- Separate tables per app workflow

---

## 📚 Related Documentation

- Live Apps: `../3_Live_Apps/docs/README.md` (3 deployed apps)
- Lakebase Setup: `../3_Live_Apps/LAKEBASE_SETUP_README.md`
- Platform Observability: `../1_Platform_Observability/`

---

## 🎯 When to Use Each Template

**Inventory Command Center** → Approval workflows, action buttons  
**Demand Forecasting** → ML dashboards, forecasting  
**Dynamic Pricing API** → REST APIs, pricing engines  
**Customer Insights** → Analytics dashboards, segmentation  
**Real-Time Sales Monitor** → Live KPI tracking, streaming  
**Data Quality Dashboard** → Quality monitoring, validation

---

✨ **6 templates, production patterns, FREE edition compatible!**
