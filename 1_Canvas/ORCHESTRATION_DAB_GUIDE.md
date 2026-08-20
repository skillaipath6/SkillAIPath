# Orchestration & DAB Architecture Guide
**DAB-Based Production Deployment** | **25 Orchestrators** | **Multi-Environment**

---

## 📌 Architecture Overview

**Entry Point:** `1_Canvas/StartHere.py` → Single notebook orchestrating entire platform

**Deployment:** Databricks Asset Bundles (DAB) via `databricks.yml`

**Environments:** dev, uat, prod (environment variable-driven)

---

## 🏗 DAB Configuration

**Location:** `1_Canvas/0_DevOps/Production/databricks.yml`

```yaml
bundle:
  name: sapdbx

variables:
  environment:
    description: Deployment environment (dev/uat/prod)
    default: dev
  notification_email:
    default: your-email@example.com

targets:
  dev:
    mode: development
    workspace:
      host: ${DATABRICKS_HOST}
  uat:
    mode: development
  prod:
    mode: production

resources:
  jobs:
    sap_pipeline:
      name: "SkillAIPath Pipeline (${var.environment})"
      email_notifications:
        on_failure:
          - "${var.notification_email}"
      tasks:
        - task_key: run_canvas
          notebook_task:
            notebook_path: "/Workspace/Shared/${var.environment}/SkillAIPath/1_Canvas/StartHere"
            base_parameters:
              environment: "${var.environment}"
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "Standard_DS3_v2"
            num_workers: 2
```

**Key Features:**
- Single job definition (`sap_pipeline`)
- Single task (`run_canvas`)
- Environment-driven paths
- Auto-notification on failure
- Cluster auto-provisioning

---

## 🎯 Orchestration Hierarchy

### Level 1: Main Entry Point
**`StartHere.py`** - Master orchestrator
- Initializes environment
- Calls Data Platform orchestrator
- Calls AI Platform orchestrator
- Handles cross-platform dependencies

### Level 2: Platform Orchestrators (2 files)

**Data Platform:**
`2_Orchestration/Data_Platform/1_Data_Platform_Orchestrator.py`
- Foundation setup
- Bronze layer ingestion
- Dimensions processing
- Facts processing (Part 1 & 2)
- Streaming CDC
- Gold layer (Part 1 & 2)
- DBT integration
- Governance
- Federation
- External sources

**AI Platform:**
`2_Orchestration/AI_Platform/1_AI_Platform_Orchestrator.py`
- MLOps pipeline
- RAG pipeline
- AI Agents setup
- AI Gateway configuration

### Level 3: Component Orchestrators (23 files)

#### Data Platform Components (19 files)
```
2_Foundation.py                  # Lakebase, Unity Catalog setup
3_Bronze_Layer.py                # Raw data ingestion
4_Dimensions.py                  # Dimension tables (14 files)
5_Facts_Part1.py                 # Transactional facts
6_Facts_Part2.py                 # Aggregated facts, bridge tables
7_Streaming_CDC.py               # Real-time CDC (16 files)
8_Gold_Part1.py                  # Batch marts
9_Gold_Part2.py                  # Streaming marts
10_DBT_Integration.py            # DBT models (29 files)
11_Governance.py                 # Tags, lineage, quality
12_Federation.py                 # External data sources
13_External_Sources.py           # API, file ingestion
12_Start_FullLoad.py             # Full load trigger
13_Start_IncrementalLoad.py      # Incremental load trigger
13_Start_Incremental_Load_2.py   # Incremental variant
14_StartDBT_Full.py              # DBT full refresh
15_StartDBT_Incremental.py       # DBT incremental
```

#### AI Platform Components (5 files)
```
2_MLOps.py                       # Model training/deployment (10 files)
3_RAG_Pipeline.py                # Vector DB, RAG (3 files)
4_AI_Agents.py                   # Domain agents (31 files)
5_AI_Gateway.py                  # Gateway integration
```

#### Shared Components (1 file)
```
checkpoint_framework.py          # Progress tracking, idempotency
```

---

## 🚀 Deployment Workflow

### 1. **Local Development (dev)**
```bash
# Deploy to dev
databricks bundle deploy --target dev

# Run pipeline
databricks bundle run sap_pipeline --target dev
```

### 2. **UAT Testing (uat)**
```bash
# Deploy to uat
databricks bundle deploy --target uat

# Run pipeline
databricks bundle run sap_pipeline --target uat
```

### 3. **Production (prod)**
```bash
# Deploy to prod (production mode)
databricks bundle deploy --target prod

# Run pipeline
databricks bundle run sap_pipeline --target prod
```

### Environment Isolation
- **Paths:** `/Workspace/Shared/{environment}/SkillAIPath/`
- **Catalogs:** `sap_{environment}` (e.g., `sap_dev`, `sap_prod`)
- **Clusters:** Environment-specific configurations

---

## 📦 Orchestration Patterns

### Pattern 1: Sequential Execution
```python
# Example: Data Platform Orchestrator
dbutils.notebook.run("2_Foundation", timeout_seconds=3600)
dbutils.notebook.run("3_Bronze_Layer", timeout_seconds=3600)
dbutils.notebook.run("4_Dimensions", timeout_seconds=7200)
```

### Pattern 2: Parallel Execution
```python
# Example: Facts Part 1 & 2 (independent)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    future1 = executor.submit(dbutils.notebook.run, "5_Facts_Part1", 3600)
    future2 = executor.submit(dbutils.notebook.run, "6_Facts_Part2", 3600)
```

### Pattern 3: Checkpoint-Based Idempotency
```python
# Using checkpoint_framework.py
from checkpoint_framework import CheckpointManager

cp = CheckpointManager("dimension_processing")
if not cp.is_completed("dim_customer"):
    # Process dim_customer
    cp.mark_completed("dim_customer")
```

---

## 🔧 Production Jobs

**Location:** `1_Canvas/3_Production_Jobs/Import_All_Jobs.py`

**Purpose:** Mass-import all orchestration jobs into Databricks Workflows

**Usage:**
```python
# Run Import_All_Jobs to create/update all workflow jobs
dbutils.notebook.run("3_Production_Jobs/Import_All_Jobs", 600)
```

**Generates:**
- 25 individual workflow jobs (one per orchestrator)
- Dependency chains
- Retry logic
- Email notifications
- Cluster configurations

---

## 🧪 Testing Orchestrators

### Test Individual Component
```bash
# From notebook or DAB
dbutils.notebook.run("1_Canvas/2_Orchestration/Data_Platform/4_Dimensions", 3600)
```

### Test Full Platform
```bash
# Run entire Data Platform
dbutils.notebook.run("1_Canvas/2_Orchestration/Data_Platform/1_Data_Platform_Orchestrator", 14400)
```

### Test End-to-End
```bash
# Run complete pipeline
databricks bundle run sap_pipeline --target dev
```

---

## 📊 Orchestration Metrics

**Total Orchestrators:** 25 files
- Data Platform: 19 orchestrators
- AI Platform: 5 orchestrators
- Shared: 1 framework

**Total Components:**
- Dimensions: 14 files
- Facts: 10 files (4 core + 3 bridge + 3 patterns)
- Gold: 9 files (4 batch + 4 streaming + 1 spec)
- Streaming CDC: 16 files
- DBT Models: 29 SQL files
- MLOps: 10 files
- AI Agents: 31 files
- Quality Ops: 23 files

---

## 🐛 Troubleshooting

**Job fails on deploy:**
- Verify `databricks.yml` syntax
- Check environment variables
- Confirm workspace host

**Orchestrator timeout:**
- Increase `timeout_seconds` in DAB config
- Check cluster size (num_workers)
- Review component dependencies

**Path not found:**
- Verify `/Workspace/Shared/{environment}/SkillAIPath/` exists
- Check environment variable passed correctly
- Confirm notebook paths in DAB config

**Checkpoint issues:**
- Clear checkpoints: `CheckpointManager.reset_all()`
- Check Unity Catalog table access
- Verify idempotency logic

---

## 💡 Best Practices

1. **Use DAB for all deployments** - Avoid manual job creation
2. **Environment isolation** - Never mix dev/uat/prod data
3. **Checkpoint framework** - Ensure idempotency for all orchestrators
4. **Timeout buffers** - Set 2x expected runtime
5. **Notification setup** - Always configure failure alerts
6. **Version control** - All DAB configs in Git
7. **Test in dev first** - Never deploy directly to prod
8. **Monitor execution** - Use StartHere logs for end-to-end view

---

## 🔗 Related Documentation

- **DAB Setup Guide:** `1_Canvas/0_DevOps/Production/SETUP_GUIDE.md`
- **Job Descriptions:** `1_Canvas/0_DevOps/Production/JOB_DESCRIPTION.md`
- **Checkpoint Framework:** `1_Canvas/2_Orchestration/checkpoint_framework.py`
- **Import All Jobs:** `1_Canvas/3_Production_Jobs/Import_All_Jobs.py`

---

## 📅 Execution Schedule

**Typical Production Schedule:**
- **Full Load:** Weekly (Sunday 2 AM)
- **Incremental Load:** Daily (Every 4 hours)
- **DBT Incremental:** Hourly
- **Streaming CDC:** Continuous (Auto Loader)
- **ML Retraining:** Daily (Post data refresh)

**DAB Trigger:**
```bash
# Schedule via DAB
databricks jobs create --json @schedule.json
```

---

✨ **Production-ready, DAB-based, multi-environment orchestration!**
