# SkillAI Path - Production Jobs Portfolio

## Overview
21 production-ready jobs organized in 4 categories, all with consistent naming (01-20) and file names matching job names.

---

## 🆕 NEW AUTOMATION CAPABILITIES

### 1⃣ Portfolio GitHub AutoCommit (Job 19)
**Monthly automation for portfolio updates**

**What it does:**
- **Collects** all production updates from the month:
  - New notebooks created
  - Jobs deployed
  - Dashboards published
  - ML models trained
  - Pipeline updates
  
- **Generates** portfolio markdown with:
  - Live metrics (job success rates, data volumes, model performance)
  - Tech stack showcase
  - Production deployments timeline
  - Links to live dashboards and endpoints

- **Auto-commits** to GitHub with:
  - Professional commit messages
  - Monthly progress snapshots
  - Real production evidence
  - Automated contribution graph updates

**Schedule:** 1st of every month, 10AM UTC (PAUSED - enable when ready)

**Workflow:**
1. Collect_production_updates → Scan workspace for changes
2. Generate_portfolio_markdown → Create beautiful README
3. GitHub_auto_commit → Push with credentials

**Use Case:**
"Every month, this job automatically updates your GitHub portfolio with REAL production work - no manual copy-paste. Recruiters see live deployments, not claims."

---

### 2⃣ Genie Space Creator (Job 20)
**Automated Genie Space provisioning from catalogs**

**What it does:**
- **Scans** all Unity Catalog catalogs in workspace
- **Creates** Genie Spaces automatically for each catalog/schema
- **Seeds** initial conversations with:
  - Sample questions about the data
  - Table relationships
  - Common analytics patterns
  - Data dictionary summaries

**Workflow:**
1. Scan_catalogs → Discover all UC catalogs and schemas
2. Create_genie_spaces → Provision spaces with proper permissions
3. Seed_initial_conversations → Add starter prompts and documentation

**Benefits:**
- **Eliminates manual space creation** - No more clicking through UI
- **Consistent setup** - Every space has standard starter questions
- **Self-service analytics** - Business users get instant query interface
- **Scales automatically** - New catalogs get spaces automatically

**Use Case:**
"When you create a new catalog 'sales_analytics', this job automatically creates a Genie Space, connects it, and seeds it with 10 starter questions like 'Show top products by revenue' - ready for business users immediately."

---

##  Directory Structure

```
/Shared/dev/SkillAIPath/1_Canvas/3_Production_Jobs/
│
├── 00_StartHere.Json                    [Dev→UAT→Prod pipeline]
│
├── DevOps & Infrastructure
│   ├── 01_DevOps.Json                   [GitHub automation]
│   ├── 02_EduFin_Core_Analytics.Json    [Business analytics]
│   ├── 16_App_Deployment.Json           [App deployment]
│   ├── 19_Portfolio_GitHub_AutoCommit.Json  ⭐ NEW
│   └── 20_Genie_Space_Creator.Json      ⭐ NEW
│
├── Data Platform
│   ├── 03_Lakehouse_Full_Load.Json
│   ├── 04_Lakehouse_Incremental.Json    ⭐ NEW
│   ├── 05_DBT_Full_Transformation.Json
│   ├── 06_DBT_Incremental.Json          ⭐ NEW
│   ├── 07_Streaming_CDC_Pipeline.Json
│   ├── 08_Bronze_Silver_DLT_Pipeline.Json
│   ├── 15_Daily_Incremental_Refresh.Json
│   └── 17_Lakebase_Sync.Json
│
├── ML/AI Models
│   ├── 09_Churn_Prediction_Model.Json
│   ├── 10_Product_Recommendation_Model.Json
│   ├── 11_Demand_Forecasting_Model.Json
│   ├── 12_Next_Purchase_Prediction.Json
│   ├── 13_ML_Platform_Orchestrator.Json
│   └── 14_AI_Training_Data_Extraction.Json
│
└── Master Orchestration
    └── 18_Master_SkillAI_Weekly.Json    [Weekly full pipeline]
```

---

## Production Deployment Strategy

### Phase 1: Foundation (Week 1)
1. Run **00_StartHere** - Validate Dev→UAT→Prod flow
2. Run **03_Lakehouse_Full_Load** (one-time)
3. Run **05_DBT_Full_Transformation** (one-time)

### Phase 2: Incremental (Week 2)
4. Enable **15_Daily_Incremental_Refresh** (6AM UTC daily)
5. Test **04_Lakehouse_Incremental** manually
6. Test **06_DBT_Incremental** manually

### Phase 3: ML Platform (Week 3)
7. Run individual ML jobs (09-12) manually
8. Validate **13_ML_Platform_Orchestrator** (runs all 4 in parallel)

### Phase 4: Automation (Week 4)
9. Enable **18_Master_SkillAI_Weekly** (Sundays 2AM UTC)
10. Test **19_Portfolio_GitHub_AutoCommit** manually
11. Test **20_Genie_Space_Creator** manually

### Phase 5: Full Automation (Month 2)
12. Enable **19_Portfolio_GitHub_AutoCommit** (monthly on 1st)
13. Run **20_Genie_Space_Creator** on-demand when new catalogs added

---

## Quick Start Commands

### View all jobs:
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

for job in w.jobs.list():
    if any(x in job.settings.name for x in ['DevOps', 'EduFin', 'Lakehouse', 'DBT', 'ML', 'SkillAI']):
        print(f"[{job.job_id}] {job.settings.name}")
```

### Run a specific job:
```python
# Example: Run Portfolio GitHub AutoCommit
job_id = 180498276460024
run = w.jobs.run_now(job_id)
print(f"Started run: {run.run_id}")
```

---

## Key Metrics to Track

### Data Platform Health:
- Daily Incremental Success Rate
- DBT model execution time
- DLT pipeline latency
- Data quality check failures

### ML Platform Performance:
- Model training duration
- Model accuracy metrics
- Feature freshness
- Prediction latency

### DevOps Automation:
- GitHub commit frequency
- Portfolio update completeness
- Genie Space creation success rate
- App deployment time

---

## Prerequisites

### For Portfolio GitHub AutoCommit:
- GitHub personal access token (stored in Databricks Secrets)
- Repository write permissions
- Workspace read permissions for job/notebook scanning

### For Genie Space Creator:
- Unity Catalog USAGE permissions
- Genie Space creation permissions
- Catalog metadata read access

---

## Notes

- All jobs use **serverless compute** by default (queue enabled)
- All jobs write to **/Shared/dev** workspace (not Users folder)
- Job names match file names for easy correlation
- Numeric prefixes (01-20) maintain execution order
- PAUSED jobs require manual enable when ready for production

---

**Last Updated:** 2026-08-13 17:59 UTC
**Status:** All 21 jobs LIVE in production
**View Jobs:** https://dbc-d7a68efa-ffba.cloud.databricks.com/#joblist
