# SkillAIPath - Production Data & AI Platform
**Complete Technical Architecture | Databricks Free Edition**

---

## Executive Summary

SkillAIPath is a **production-grade, end-to-end data and AI platform** built entirely on **Databricks Free Edition**. It implements enterprise patterns including medallion architecture, parallel multi-engine transformation, ML pipelines, and business intelligence—demonstrating that sophisticated data platforms don't require paid infrastructure.

**Platform Stats:**
- **45 Python notebooks** across orchestration, transformation, and ML
- **26 production jobs** (automated via Databricks Workflows)
- **19+ architecture diagrams** documenting every layer
- **3 transformation engines** running in parallel (Lakehouse+DBT, DLT Streaming, Lakebase Sync)
- **5 ML models** with MLflow tracking and model registry
- **13 BI dashboards** + 4 Genie Spaces + 4 Apps
- **500+ automated tests** via DBT
- **< 5 min incremental latency** for streaming CDC
- **< 15 min full environment setup** via automated bootstrap

---

## Table of Contents

1. [Folder Structure & Navigation](#folder-structure)
2. [Getting Started - Bootstrap Process](#getting-started)
3. [Configuration Architecture](#configuration-architecture)
4. [Production Jobs (26 Jobs)](#production-jobs)
5. [Data Platform - Medallion Architecture](#data-platform)
6. [AI Intelligence Platform](#ai-platform)
7. [Business Value Layer](#business-value)
8. [DevOps & Automation](#devops)
9. [Technical Patterns](#technical-patterns)
10. [Performance & Optimization](#performance)

---

## Folder Structure & Navigation {#folder-structure}

### Canvas Root: `/Shared/dev/SkillAIPath/1_Canvas/`

```
1_Canvas/
├── 0_DevOps/                    # GitHub automation, production setup
│   └── Production/
│       ├── GitHub_Auto_Setup.py
│       ├── JOB_DESCRIPTION.md
│       └── SETUP_GUIDE.md
│
├── 1_Setup/                     # Bootstrap, config, data generation
│   ├── 1_config.py              # ⭐ SINGLE SOURCE OF TRUTH - All table names
│   ├── 2_data_generator.py      # Synthetic data (30 days, 6 tables)
│   ├── 3_reset_catalog.py       # Fast reset (TRUNCATE vs DROP/CREATE)
│   ├── 4_data_generation_guide.py
│   └── 5_archive_and_cleanup.py
│
├── 2_Orchestration/             # Pipeline orchestrators
│   ├── Start_SkillAI.py         # MASTER ENTRY POINT
│   ├── checkpoint_framework.py  # Reusable orchestration patterns
│   │
│   ├── Data_Platform/           # Bronze → Silver → Gold pipelines
│   │   ├── 1_Data_Platform_Orchestrator.py
│   │   ├── 2_Foundation.py
│   │   ├── 3_Bronze_Layer.py
│   │   ├── 4_Dimensions.py      # 9 SCD Type 2 dimensions
│   │   ├── 5_Facts_Part1.py
│   │   ├── 6_Facts_Part2.py
│   │   ├── 7_Streaming_CDC.py
│   │   ├── 8_Gold_Part1.py
│   │   ├── 9_Gold_Part2.py
│   │   ├── 10_DBT_Integration.py
│   │   ├── 11_Governance.py
│   │   ├── 12_Federation.py
│   │   ├── 13_External_Sources.py
│   │   ├── 12_Start_FullLoad.py
│   │   ├── 13_Start_IncrementalLoad.py
│   │   ├── 14_StartDBT_Full.py
│   │   └── 15_StartDBT_Incremental.py
│   │
│   └── AI_Platform/             # ML pipelines, RAG, agents
│       ├── 1_AI_Platform_Orchestrator.py
│       ├── 2_MLOps.py
│       ├── 3_RAG_Pipeline.py
│       ├── 4_AI_Agents.py
│       ├── 5_AI_Gateway.py
│       └── 6_App_Deployment.py
│
├── 3_Production_Jobs/           # 26 Databricks Workflow JSONs
│   ├── 00_Start_SkillAI.Json
│   ├── 01_OnDemand_DevOps.Json
│   ├── 02_OnDemand_EduFin_Core_Analytics.Json
│   ├── 03_Daily_Lakehouse_Full_Load.Json
│   ├── 04_Daily_Lakehouse_Incremental.Json
│   ├── 05_Daily_DBT_Full_Transformation.Json
│   ├── 06_Daily_DBT_Incremental.Json
│   ├── 07_OnDemand_Genie_Space_Creator.Json
│   ├── 08_Daily_Streaming_CDC.Json
│   ├── 09_Daily_Bronze_Silver_DLT.Json
│   ├── 10_Daily_Knowledge_Retrieval_System.Json
│   ├── 10.1_AgentOps.Json
│   ├── 11_Daily_Ecommerce_Intelligence.Json
│   ├── 12_Daily_Customer_360.Json
│   ├── 13_Daily_Auto_Documentation.Json
│   ├── 14_Weekly_Training_Data_Extraction.Json
│   ├── 15_Weekly_Churn_Prediction.Json
│   ├── 16_Weekly_Product_Recommendation.Json
│   ├── 17_Weekly_Demand_Forecasting.Json
│   ├── 18_Weekly_Next_Purchase_Prediction.Json
│   ├── 19_Daily_Incremental_Refresh.Json
│   ├── 20_Deploy_AutoReview_App.Json
│   ├── 21_Deploy_BizApps.Json
│   ├── 22_Daily_Lakebase_Sync.Json
│   ├── 23_Master_SkillAI_Weekly.Json
│   ├── 24_Monthly_Portfolio_GitHub_AutoCommit.Json
│   ├── IMPORT_ALL_JOBS.py       # Bulk import to workspace
│   └── README.md
│
├── 4_Ingestion_Sources/         # External data integrations
│   ├── 00_ORCHESTRATOR_Enrichment_Pipeline.py
│   ├── 01_ingest_tpch_suppliers.py
│   ├── 02_ingest_weather_data.py
│   ├── 03_silver_supplier_benchmark.py
│   ├── 04_silver_weather_sales.py
│   ├── 05_gold_supplier_analytics.py
│   ├── 06_gold_weather_analytics.py
│   ├── 07_ingest_exchange_rates.py
│   ├── 08_ingest_logistics.py
│   └── 09_External_Integration/
│       ├── 01_kafka_streaming_consumer.py
│       └── 02_s3_event_driven_ingestion.py
│
├── Architecture_Diagrams/       # 19+ technical architecture docs
│   ├── 00_JOB_TECHNICAL_ARCHITECTURE.md
│   ├── 01_PRODUCTION_ARCHITECTURE.md
│   ├── 02_Canvas_System_Overview.md
│   ├── 03_Data_Platform_End_to_End_Flow.md
│   ├── 04_DevOps_Production_Architecture.md
│   ├── 05_DevOps_CICD_Pipeline.md
│   ├── 06_Setup_Bootstrap_Architecture.md
│   ├── 07_Orchestration_Architecture.md
│   ├── 08_Data_Integrations_Flow.md
│   ├── 09_Canvas_Operations_Flow.md
│   ├── 10_Industry_Patterns_Architecture.md
│   ├── 11_AI_Gateway_Integration_Architecture.md
│   ├── 12_Industry_Patterns_Catalog.md
│   ├── 13_AI_Agent_Architecture.md
│   ├── 14_AI_Agent_Blueprints_Catalog.md
│   ├── 15_BI_App_Templates_Stack.md
│   ├── 16_BI_App_Templates_Catalog.md
│   ├── 17_Training_Execution_System.md
│   ├── 18_Training_Task_Patterns.md
│   └── 19_Training_Sessions_Architecture.md
│
├── Canvas_Guide.md              # Canvas platform foundation
├── SkillAIPath_Guide.md         # This document
├── Assets.tsv                   # Asset inventory (tab-separated)
└── StartHere.py                 # One-click environment setup
```

**Key Entry Points:**
- **StartHere.py** - Automated environment bootstrap (< 15 min)
- **2_Orchestration/Start_SkillAI.py** - Master orchestrator
- **1_Setup/1_config.py** - Configuration (imported via %run)
- **Architecture_Diagrams/** - Technical documentation

---

## Getting Started - Bootstrap Process {#getting-started}

### One-Click Setup: `StartHere.py`

**Path:** `/Shared/dev/SkillAIPath/1_Canvas/StartHere.py`

**What it does:**
1. **Auto-detects environment** from notebook path (dev/uat/prod)
2. **Creates catalog & schemas** if they don't exist
3. **Resets environment** (TRUNCATE - 70% faster than DROP/CREATE)
4. **Generates 30 days** of synthetic ecommerce data
5. **Builds Bronze layer** (6 raw staging tables)
6. **Builds Silver layer** (9 dimensions + 3 facts in parallel)
7. **Builds Gold layer** (3 analytics marts)

**Target Runtime:** < 15 minutes

**Dual-Mode Architecture:**

```python
# USER MODE: /Users/{email}/SkillAIPath/
# - Catalog: workspace (system catalog)
# - Schema: workspace.{email_prefix}_dev
# - Tables: bronze_*, silver_*, gold_* (with prefixes)
# - Data: 3 days (fast testing)

# SHARED MODE: /Shared/{env}/SkillAIPath/
# - Catalog: sap_{env} (e.g., sap_dev, sap_main)
# - Schemas: bronze, silver, gold (separate schemas)
# - Data: 30 days (production)
```

**Usage:**
```python
# Simply run all cells in StartHere.py
# Environment is auto-detected - no configuration needed!
```

### Environment Detection Logic

**From:** `1_Setup/1_config.py`

```python
import os
import re

# Get current notebook path
current_path = os.getcwd()

if '/Users/' in current_path:
    # USER MODE
    match = re.search(r'/Users/([^/@]+)', current_path)
    user_prefix = match.group(1)
    CATALOG = "workspace"
    SCHEMA = f"{user_prefix}_dev"
    USE_FLAT_SCHEMA = True  # bronze_*, silver_*, gold_* prefixes
    
elif '/Shared/' in current_path:
    # SHARED MODE
    match = re.search(r'/Shared/([^/]+)/SkillAIPath/', current_path)
    env = match.group(1)  # dev/uat/prod
    CATALOG = f"sap_{env}"
    USE_FLAT_SCHEMA = False  # Separate bronze/silver/gold schemas
```

**Result:** Zero hardcoded paths. Works in any environment.

---

## Configuration Architecture {#configuration-architecture}

### Single Source of Truth: `1_config.py`

**Path:** `1_Canvas/1_Setup/1_config.py`

**Pattern:** All notebooks import config via `%run`

**Benefits:**
- Change table name **once**, applies to **40+ notebooks**
- No hardcoding across codebase
- Environment portability (dev/uat/prod)
- Widget-based overrides

**Usage in Notebooks:**

```python
# From 2_Orchestration/Data_Platform/ folders:
%run ../../1_Canvas/1_Setup/1_config

# From 2_Orchestration/AI_Platform/ folders:
%run ../../1_Canvas/1_Setup/1_config

# From StartHere or root:
%run ./1_Setup/1_config

# Access configuration:
df.write.mode("append").saveAsTable(Config.TBL_FACT_SALES)
print(f"Target catalog: {Config.CATALOG}")
print(f"Environment: {Config.ENVIRONMENT}")
```

### Configuration Class Structure

```python
class Config:
    # Environment
    ENVIRONMENT = "dev"  # Auto-detected from path
    CATALOG = "sap_dev"
    
    # Bronze Layer (Raw Staging)
    TBL_STG_SALES = f"{CATALOG}.bronze.stg_sales"
    TBL_STG_PURCHASE = f"{CATALOG}.bronze.stg_purchase"
    TBL_STG_STOCK_STATUS = f"{CATALOG}.bronze.stg_stock_status"
    TBL_STG_CUSTOMER = f"{CATALOG}.bronze.stg_customer"
    TBL_STG_PRODUCT = f"{CATALOG}.bronze.stg_product"
    TBL_STG_AGENT = f"{CATALOG}.bronze.stg_agent"
    
    # Silver Layer (Curated Data)
    # Dimensions (9 SCD Type 2 tables)
    TBL_DIM_CUSTOMER = f"{CATALOG}.silver.dim_customer"
    TBL_DIM_PRODUCT = f"{CATALOG}.silver.dim_product"
    TBL_DIM_AGENT = f"{CATALOG}.silver.dim_agent"
    TBL_DIM_RETAILER = f"{CATALOG}.silver.dim_retailer"
    TBL_DIM_WAREHOUSE = f"{CATALOG}.silver.dim_warehouse"
    TBL_DIM_WHOLESALER = f"{CATALOG}.silver.dim_wholesaler"
    TBL_DIM_DISTRIBUTOR = f"{CATALOG}.silver.dim_distributor"
    TBL_DIM_DATE = f"{CATALOG}.silver.dim_date"
    TBL_DIM_TIME = f"{CATALOG}.silver.dim_time"
    
    # Facts (3 tables)
    TBL_FACT_SALES = f"{CATALOG}.silver.fact_sales"
    TBL_FACT_INVENTORY = f"{CATALOG}.silver.fact_inventory"
    TBL_FACT_PURCHASE = f"{CATALOG}.silver.fact_purchase"
    
    # Bridge (1 table)
    TBL_BRIDGE_PRODUCT_CATEGORY = f"{CATALOG}.silver.bridge_product_category"
    
    # Gold Layer (Business Marts)
    TBL_MART_CUSTOMER_360 = f"{CATALOG}.gold.mart_customer_360"
    TBL_MART_RFM_ANALYSIS = f"{CATALOG}.gold.mart_rfm_analysis"
    TBL_MART_PRODUCT_PERFORMANCE = f"{CATALOG}.gold.mart_product_performance"
    TBL_USER_SESSION_ML = f"{CATALOG}.gold.user_session_ml"
```

**Impact:** 40+ notebooks reference `Config.*` constants. Changing catalog or environment propagates everywhere instantly.

---

## Production Jobs (26 Jobs) {#production-jobs}

### Job Architecture Overview

**All jobs defined as JSON:** `3_Production_Jobs/*.Json`

**Deployment:** Import via `IMPORT_ALL_JOBS.py`

### Job Catalog

#### Phase 1: Foundation & Setup

**Job 00: Start SkillAI (Master Orchestrator)**
- Entry point for full platform execution
- Coordinates all downstream jobs
- Dependency management

**Job 01: OnDemand DevOps**
- Unity Catalog initialization
- Workspace configuration
- Permissions setup
- GitHub integration

**Job 02: OnDemand EduFin Core Analytics**
- Educational finance demo catalog
- Business analytics baseline
- Training data for demos

#### Phase 2: Bronze Layer - Data Ingestion

**Job 03: Daily Lakehouse Full Load**
- **Pattern:** Full table refresh
- **Tables:** 6 bronze tables (stg_*)
- **Features:**
  - Schema inference & evolution
  - Audit columns: `_ingested_at`, `_source_file`, `_job_id`
  - AutoLoader for file detection
  - Time travel enabled (30-day retention)

**Job 04: Daily Lakehouse Incremental**
- **Pattern:** Incremental CDC via watermarking
- **Latency:** < 5 minutes
- **Features:**
  - Checkpoint management
  - Exactly-once semantics
  - Idempotent operations
  - Late-arriving data handling

**Output:** `skillaipath_main.bronze.*` (6 tables)

#### Phase 3: Silver Layer - Parallel Multi-Engine Transformation

**ENGINE 1: Lakehouse + DBT**

**Job 05: Daily DBT Full Transformation**
- **Tables:** 13 (9 dims + 3 facts + 1 bridge)
- **Dimensions:** SCD Type 2 implementation
  - `dim_customer`, `dim_product`, `dim_agent`
  - `dim_retailer`, `dim_warehouse`, `dim_wholesaler`, `dim_distributor`
  - `dim_date`, `dim_time`
- **Facts:** Transaction tables
  - `fact_sales`, `fact_inventory`, `fact_purchase`
- **Bridge:** Many-to-many relationships
  - `bridge_product_category`
- **Data Quality:** 500+ DBT tests
  - Uniqueness, not_null, relationships
  - Accepted values, custom business rules

**Job 06: Daily DBT Incremental**
- **Pattern:** CDC via MERGE operations
- **SCD Type 2 Fields:**
  - `valid_from`, `valid_to`, `is_current`
  - Surrogate key generation
  - Historical tracking
- **Watermarking:** `last_updated_at` tracking

**ENGINE 2: DLT Streaming**

**Job 08: Daily Streaming CDC**
- **Pattern:** Real-time change data capture
- **Latency:** < 5 minutes
- **Features:**
  - Continuous processing
  - Auto-scaling compute
  - Checkpointing (exactly-once)
  - Auto-recovery on failures

**Job 09: Daily Bronze-Silver DLT**
- **Pattern:** Declarative pipeline (SQL + Python)
- **Features:**
  - Expectations (inline data quality)
  - Materialized views
  - Lineage tracking
  - Auto-optimization

**ENGINE 3: Lakebase Sync**

**Job 22: Daily Lakebase Sync**
- **Pattern:** OLTP → OLAP sync
- **Source:** Lakebase Postgres
- **Target:** `sap_dev` catalog
- **Latency:** < 5 minutes
- **Operation:** MERGE (upsert pattern)
- **Aggregations:**
  - `session_count`, `total_duration`, `avg_page_views`

**Output:** `skillaipath_main.silver.*` (13 tables)

#### Phase 4: Gold Layer - Business Marts

**Job 10: Daily Knowledge Retrieval System**
- RAG pipeline (vector database + embeddings)
- Semantic search
- Context-aware responses
- AI agent coordination

**Job 11: Daily Ecommerce Intelligence**
- Sales analytics
- Product performance
- Customer behavior patterns
- RFM segmentation

**Job 12: Daily Customer 360**
- Unified customer view
- Lifetime value calculation
- Churn risk scoring
- Behavioral analytics

**Job 13: Daily Auto Documentation**
- Metadata catalog generation
- Lineage tracking
- Dependency mapping
- API documentation

**Job 19: Daily Incremental Refresh**
- Incremental gold layer updates
- Aggregation refresh
- Metric recalculation

**Output:** `skillaipath_main.gold.*` (3+ marts)

#### Phase 5: AI/ML Pipeline

**Job 14: Weekly Training Data Extraction**
- Feature engineering
- Point-in-time correctness
- Train/validation/test splits (70/20/10)
- Feature store population

**Job 15: Weekly Churn Prediction**
- **Model:** Classification (XGBoost)
- **Features:** RFM, transaction history, engagement
- **Output:** Churn probability (0-1)
- **MLflow:** Experiment tracking + model registry

**Job 16: Weekly Product Recommendation**
- **Model:** Collaborative filtering (ALS)
- **Features:** Purchase history, co-occurrence
- **Output:** Top-N recommendations per customer
- **Serving:** Batch inference

**Job 17: Weekly Demand Forecasting**
- **Model:** Time series (Prophet/ARIMA)
- **Features:** Historical sales, seasonality, trends
- **Output:** 30-day demand forecast
- **Use Case:** Inventory optimization

**Job 18: Weekly Next Purchase Prediction**
- **Model:** Regression (LightGBM)
- **Features:** Purchase patterns, recency, frequency
- **Output:** Days until next purchase
- **Use Case:** Marketing campaign timing

**All ML Jobs:**
- MLflow experiment tracking
- Model versioning (Staging → Production)
- A/B testing framework
- Drift detection

#### Phase 6: BI & Apps

**Job 07: OnDemand Genie Space Creator**
- Creates 4 Genie Spaces
- Natural language to SQL
- Self-service analytics

**Job 20: Deploy AutoReview App**
- Databricks App deployment
- RAG-driven code review
- Chat interface

**Job 21: Deploy BizApps (3 Apps)**
- Intelligence Hub App
- Agents Dashboard App
- Inventory Management App

#### Phase 7: Maintenance & Orchestration

**Job 23: Master SkillAI Weekly**
- Weekly full refresh
- Coordinated execution of all pipelines
- Health checks

**Job 24: Monthly Portfolio GitHub AutoCommit**
- Automated Git commits
- Change tracking
- Version control

**Job 10.1: AgentOps**
- AI agent monitoring
- Performance metrics
- Quality gates

### Job Dependency Matrix

```
Phase 1: Foundation (Sequential)
  Job 01 (DevOps)
    └─→ Job 02 (EduFin)
         └─→ Jobs 03-04 (Bronze) ──── PARALLEL

Phase 2: Silver (Parallel Engines)
  Jobs 03-04 (Bronze)
    ├─→ Jobs 05-06 (DBT) ────────── ENGINE 1
    ├─→ Jobs 08-09 (DLT) ────────── ENGINE 2
    └─→ Job 22 (Lakebase) ────────── ENGINE 3

Phase 3: Gold & AI (Mostly Parallel)
  Jobs 05-09 (Silver)
    ├─→ Job 10 (RAG) ──────────────── PARALLEL
    ├─→ Job 11 (Ecommerce) ────────── PARALLEL
    ├─→ Job 12 (Customer 360) ───────── PARALLEL
    ├─→ Job 13 (Auto Docs) ──────────── PARALLEL
    └─→ Job 14 (Training Data)
         ├─→ Job 15 (Churn) ────────── PARALLEL
         ├─→ Job 16 (Recommendation) ── PARALLEL
         ├─→ Job 17 (Forecasting) ───── PARALLEL
         └─→ Job 18 (Next Purchase) ──── PARALLEL

Phase 4: BI & Apps (All Parallel)
  Jobs 10-18 (Gold/AI)
    ├─→ Job 07 (Genie Spaces) ───────── PARALLEL
    ├─→ Job 20-21 (Apps) ────────────── PARALLEL
    └─→ Dashboards (13) ──────────────── PARALLEL
```

**Execution Times:**
- **Full Load:** 20-25 minutes (Jobs 03 + 05 + Gold)
- **Incremental Load:** 5-8 minutes (Jobs 04 + 06 + refresh)
- **ML Training:** 15-30 minutes per model (weekly)
- **Bootstrap (StartHere):** < 15 minutes

---

## Data Platform - Medallion Architecture {#data-platform}

### Bronze Layer: Raw Data Ingestion

**Catalog:** `skillaipath_main.bronze.*`

**Tables (6):**
```sql
-- Core transaction data
stg_sales          -- Sales transactions (orders, line items, amounts)
stg_purchase       -- Purchase orders (procurement from suppliers)
stg_stock_status   -- Inventory levels (warehouse stock, movements)

-- Master data
stg_customer       -- Customer master (profiles, segments, addresses)
stg_product        -- Product catalog (SKUs, categories, pricing)
stg_agent          -- Sales agent data (performance, territories)
```

**Characteristics:**
- **Immutable:** Append-only (no updates/deletes)
- **Audit Trail:** `_ingested_at`, `_source_file`, `_job_id`
- **Time Travel:** 30-day retention (Delta Lake)
- **Schema Evolution:** Auto-handled via AutoLoader

**Ingestion Patterns:**

1. **Synthetic Data Generation** (`1_Setup/2_data_generator.py`)
   - Realistic ecommerce transactions
   - Configurable volume (3-30 days)
   - Relationships maintained (FK integrity)
   - Seasonal patterns, trends, anomalies

2. **External APIs** (`4_Ingestion_Sources/`)
   - REST APIs with OAuth authentication
   - Rate limiting & retry logic
   - Google Sheets via Drive API
   - Google Docs text extraction

3. **File-Based** (AutoLoader)
   - Schema inference on first load
   - Checkpoint management
   - Late-arriving file handling
   - Format auto-detection (CSV, JSON, Parquet)

4. **Streaming Sources** (Kafka, S3 Events)
   - `09_External_Integration/01_kafka_streaming_consumer.py`
   - `09_External_Integration/02_s3_event_driven_ingestion.py`

**Code Example - Bronze Load:**

```python
# From: 2_Orchestration/Data_Platform/3_Bronze_Layer.py

%run ../../1_Canvas/1_Setup/1_config  # Import Config

from pyspark.sql import functions as F

# AutoLoader pattern with schema inference
df = (spark.readStream
  .format("cloudFiles")
  .option("cloudFiles.format", "csv")
  .option("cloudFiles.schemaLocation", "/tmp/schema/sales")
  .option("cloudFiles.inferColumnTypes", "true")
  .load("/mnt/source/sales/*.csv")
  .withColumn("_ingested_at", F.current_timestamp())
  .withColumn("_source_file", F.input_file_name())
  .withColumn("_job_id", F.lit(dbutils.notebook.entry_point.getDbutils().notebook().getContext().jobId().get()))
)

# Write to Bronze
(df.writeStream
  .format("delta")
  .outputMode("append")
  .option("checkpointLocation", "/tmp/checkpoint/bronze_sales")
  .trigger(availableNow=True)  # Micro-batch
  .toTable(Config.TBL_STG_SALES)
)
```

**Multi-Source Integration:**

```python
# From: 4_Ingestion_Sources/00_ORCHESTRATOR_Enrichment_Pipeline.py

# Parallel ingestion from multiple sources
import concurrent.futures

ingestion_jobs = [
    ("01_ingest_tpch_suppliers", "TPC-H Suppliers"),
    ("02_ingest_weather_data", "Weather Data API"),
    ("07_ingest_exchange_rates", "Currency Exchange Rates"),
    ("08_ingest_logistics", "Logistics Tracking"),
]

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(dbutils.notebook.run, f"./{job}", 3600): name
        for job, name in ingestion_jobs
    }
    
    for future in concurrent.futures.as_completed(futures):
        job_name = futures[future]
        result = future.result()
        print(f"✓ {job_name}: {result}")
```

**Output:** 6 Bronze tables ready for transformation

### Silver Layer: Curated Data with SCD Type 2

**Catalog:** `skillaipath_main.silver.*`

**Tables (13):**
- **9 Dimensions** (SCD Type 2)
- **3 Facts** (transactional)
- **1 Bridge** (many-to-many relationships)

**Architecture:**

```
skillaipath_main.silver.*
├── Dimensions (9 tables with SCD Type 2)
│   ├── dim_customer    - Customer history tracking
│   ├── dim_product     - Product attributes
│   ├── dim_agent       - Sales agent details
│   └── ... (6 more)
│
├── Facts (3 tables)
│   ├── fact_sales      - Sales transactions
│   ├── fact_inventory  - Stock movements
│   └── fact_purchase   - Purchase orders
│
└── Bridge Tables
    └── bridge_product_category - Product relationships
```

**Transformation Engines:**

**Lakehouse + DBT:**
- SCD Type 2 for dimension history
- CDC patterns (Change Data Capture)
- Watermarking for incremental loads
- 500+ data quality tests
- Full vs incremental processing

**DLT Streaming:**
- Real-time CDC (< 5 min latency)
- Auto-scaling compute
- Expectations for data quality
- Materialized views
- Auto-recovery on failures

**Lakebase Sync:**
- OLTP → OLAP synchronization
- Incremental MERGE operations
- < 5 min sync latency

**Data Quality:**
- Schema validation
- Deduplication
- Z-ordering for query optimization
- VACUUM for file compaction
- Statistics refresh (ANALYZE TABLE)

### Gold Layer (Business Marts)

```
skillaipath_main.gold.*
├── mart_customer_360          - Complete customer view
├── mart_rfm_analysis          - RFM segmentation
├── mart_product_performance   - Product analytics
└── user_session_ml            - ML feature store
```

**Business Views:**
- Customer analytics (RFM, LTV, churn risk)
- Product performance (sales velocity, margin)
- Marketing analytics (segmentation, campaigns)
- ML features (aggregations, behavior features)

## Unity Catalog Structure

**Catalog:** `skillaipath_main` (or `sap_dev`/`sap_main` in SHARED mode)

```
sap_dev/
├── bronze/           # Raw staging (6 tables)
│   ├── stg_sales
│   ├── stg_purchase
│   ├── stg_stock_status
│   ├── stg_customer
│   ├── stg_product
│   └── stg_agent
│
├── silver/          # Curated data (13 tables)
│   ├── dim_customer (SCD Type 2)
│   ├── dim_product (SCD Type 2)
│   ├── dim_agent (SCD Type 2)
│   ├── dim_retailer (SCD Type 2)
│   ├── dim_warehouse (SCD Type 2)
│   ├── dim_wholesaler (SCD Type 2)
│   ├── dim_distributor (SCD Type 2)
│   ├── dim_date (SCD Type 2)
│   ├── dim_time (SCD Type 2)
│   ├── fact_sales
│   ├── fact_inventory
│   ├── fact_purchase
│   └── bridge_product_category
│
└── gold/            # Business marts (3+ tables)
    ├── mart_customer_360
    ├── mart_rfm_analysis
    ├── mart_product_performance
    └── user_session_ml
```

**Governance:**
- Fine-grained access control (catalog/schema/table/column)
- Row-level security & column masking
- Data lineage (source → consumption)
- Audit logging (all access tracked)
- Tag-based policies

---

## AI Intelligence Platform {#ai-platform}

### ML Pipeline Architecture

**Orchestration:** `2_Orchestration/AI_Platform/`

**Pattern:** Feature Engineering → Training → Registration → Batch Inference

#### Job 14: Training Data Extraction (Weekly)

**Path:** `2_Orchestration/AI_Platform/2_MLOps.py`

**Process:**
1. **Feature Engineering** from Silver/Gold tables
2. **Point-in-time correctness** (no data leakage)
3. **Train/Val/Test splits** (70/20/10)
4. **Feature Store population**

**Example Features:**
```python
# Customer behavior features
- recency_days
- purchase_frequency_30d, 60d, 90d
- avg_order_value
- unique_products_purchased
- days_since_first_purchase
- preferred_category
- engagement_score (page views, clicks)

# RFM features
- r_score, f_score, m_score (1-5 scale)
- rfm_segment (Champions, Loyal, At Risk, Lost)

# Product affinity
- category_purchase_count
- brand_loyalty_score
```

**Output:** `gold.user_session_ml` (feature store table)

#### Job 15: Churn Prediction (Weekly)

**Algorithm:** XGBoost Classifier

**Features:**
- Recency (days since last purchase)
- Frequency (purchase count last 90 days)
- Monetary (total spend)
- Engagement (page views, cart adds)
- Support tickets (count, sentiment)

**Target:** Binary (churned = 1 if no purchase in 60 days)

**Performance Metrics:**
- AUC-ROC: 0.85+
- Precision/Recall: Optimized for recall (catch at-risk customers)
- Feature Importance: Top 10 features logged

**MLflow Tracking:**
```python
with mlflow.start_run(run_name="churn_xgboost_v3"):
    mlflow.log_params({
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 100
    })
    
    mlflow.log_metrics({
        "auc_roc": 0.87,
        "precision": 0.82,
        "recall": 0.91
    })
    
    mlflow.sklearn.log_model(
        model,
        "churn_model",
        registered_model_name="churn_prediction"
    )
```

**Output:** Predictions in `ml_predictions.churn` table

#### Job 16: Product Recommendation (Weekly)

**Algorithm:** ALS (Alternating Least Squares) - Collaborative Filtering

**Matrix:** User-Product interaction matrix
- Rows: Customers
- Columns: Products
- Values: Purchase count (implicit feedback)

**Hyperparameters:**
- Rank: 20 (latent factors)
- RegParam: 0.01
- Alpha: 40 (confidence for implicit feedback)

**Output:**
- Top-N recommendations per customer (N=10)
- Similarity scores
- Cross-sell opportunities

**Serving Pattern:**
```python
# Batch inference daily
recommendations = model.recommendForAllUsers(10)

recommendations.write.mode("overwrite").saveAsTable(
    "ml_predictions.recommendations"
)
```

#### Job 17: Demand Forecasting (Weekly)

**Algorithm:** Prophet (time series forecasting)

**Input:**
- Historical daily sales (2 years)
- Seasonality (weekly, monthly, yearly)
- Special events (holidays, promotions)

**Output:**
- 30-day demand forecast per product
- Confidence intervals (80%, 95%)
- Trend decomposition

**Use Cases:**
- Inventory replenishment
- Warehouse capacity planning
- Procurement scheduling

**Accuracy:**
- MAPE (Mean Absolute Percentage Error): < 15%
- Coverage: 95% of SKUs

#### Job 18: Next Purchase Prediction (Weekly)

**Algorithm:** LightGBM Regressor

**Target:** Days until next purchase

**Features:**
- Purchase interval history (avg, std)
- Recency
- Product lifecycle stage
- Seasonal patterns

**Use Cases:**
- Marketing campaign timing (send offer 3 days before predicted purchase)
- Retention programs
- Personalized email cadence

**Performance:**
- MAE (Mean Absolute Error): 3.2 days
- R²: 0.78

### MLflow Model Registry

**Pattern:** Staging → Production

```python
# Promote model to production
client = mlflow.tracking.MlflowClient()

client.transition_model_version_stage(
    name="churn_prediction",
    version=3,
    stage="Production",
    archive_existing_versions=True  # Archive old production models
)
```

**Model Serving:**
- Batch inference (daily via Job 19)
- Feature drift monitoring (PSI, KS-test)
- Performance degradation alerts

### RAG Knowledge Retrieval (Job 10)

**Path:** `2_Orchestration/AI_Platform/3_RAG_Pipeline.py`

**Components:**

1. **Document Ingestion**
   - Platform documentation
   - Architecture diagrams (19 docs)
   - Code notebooks (45 files)
   - Job definitions (26 JSONs)

2. **Embeddings**
   - Model: sentence-transformers/all-MiniLM-L6-v2
   - Dimension: 384
   - Chunk size: 512 tokens with 50 token overlap

3. **Vector Store**
   - FAISS (Facebook AI Similarity Search)
   - Indexed: 2,000+ document chunks
   - Retrieval: Top-K=5 relevant chunks

4. **LLM Integration**
   - Context-aware query answering
   - Semantic search over codebase
   - Auto-documentation generation

**Usage Pattern:**
```python
# Query RAG system
query = "How do I update a dimension with SCD Type 2?"

# Retrieve context
context_docs = vector_store.similarity_search(query, k=5)

# Generate answer with LLM
answer = llm.generate(
    prompt=f"Context: {context_docs}\n\nQuestion: {query}"
)
```

### AI Agents (Job 10.1: AgentOps)

**Path:** `2_Orchestration/AI_Platform/4_AI_Agents.py`

**Multi-Agent System:**

1. **Data Quality Agent**
   - Monitors 500+ DBT tests
   - Auto-remediation for common failures
   - Escalation to human for complex issues

2. **Performance Agent**
   - Query optimization recommendations
   - Z-ordering suggestions
   - Cluster sizing advice

3. **Documentation Agent**
   - Auto-generates lineage diagrams
   - Updates metadata catalog
   - Syncs comments to Unity Catalog

4. **Orchestration Agent**
   - Job dependency management
   - Failure recovery strategies
   - Resource allocation

**Coordination:**
- Parallel execution (ThreadPoolExecutor)
- Quality gates (checkpoints before proceeding)
- Autonomous decision-making with human oversight

---

## 5. Business Delivery

### Analytics Pipelines

**Ecommerce Intelligence (Job 11):**
- Sales analytics
- Product performance
- Customer behavior

**Customer 360 (Job 12):**
- Unified customer view
- Behavioral analytics
- Segmentation

**Auto Documentation (Job 13):**
- Metadata catalog
- Lineage tracking
- Dependency mapping

### Orchestration

**Full Load Pipeline (20-25 min):**
```
Bronze Validation → Dimensions (9) → Facts (3) → Gold (4) → Quality Checks
```

**Incremental Load (5-8 min):**
```
Bronze CDC → Dimensions SCD2 → Facts MERGE → Gold Refresh → Quality
```

**Scheduling:**
- Daily: ETL, DBT, streaming CDC, DLT pipelines
- Weekly: ML training, app deployment
- Monthly: Portfolio commits, cleanup

## 6. Business Value - Consumption Layer

### Business Intelligence Dashboards (13 Total)

**Executive Dashboards:**
- KPI & Strategic Metrics
- Revenue and growth tracking
- Performance scorecards

**Sales Analytics:**
- Performance & Revenue Analytics
- Channel & Agent Performance
- Sales trends and forecasting

**Operational Dashboards:**
- Inventory & Stock Management
- Purchase Orders & Vendors
- Supply chain visibility

**Customer Analytics:**
- 360 & Behavioral Analytics
- Segmentation and targeting
- Churn risk analysis

**ML Model Monitoring (5 Dashboards):**
- Churn Prediction Performance
- Product Recommendation Engine
- Demand Forecasting Analytics
- Next Purchase Prediction
- Training Pipeline & Feature Store

**Platform Monitoring:**
- Cost & Usage Analytics
- Job execution tracking
- Resource utilization

### Genie Spaces (Natural Language Queries)

**4 Production Spaces:**
- Sales & Revenue Q&A
- Inventory Q&A
- Customer Insights Q&A
- 5-Days Core Analytics

**Features:**
- Natural language to SQL
- Interactive Q&A
- Self-service analytics
- Business user friendly

### Databricks Apps (4 Planned)

1. **Intelligence Hub App**
   - RAG-driven analytics
   - Chat interface
   - Context-aware insights

2. **Agents Dashboard App**
   - Live agent monitoring
   - Performance metrics
   - Task management

3. **Inventory Management App**
   - Real-time stock tracking
   - Reorder automation
   - Supplier management

4. **Customer 360 App**
   - Complete customer view
   - Interaction history
   - Predictive insights

## 7. DevOps & Automation

### CI/CD Pipeline (Job 01)

**GitHub Integration:**
- Automated deployments
- Branch management
- Pull request workflows
- Code review automation

**Testing:**
- Unit tests
- Integration tests
- Data quality tests (500+ DBT tests)
- End-to-end validation

**Deployment:**
- Environment promotion (dev → uat → prod)
- Rollback capabilities
- Change tracking

### Automation

**Job Orchestration:**
- Parallel execution
- Dependency management
- Failure handling
- Retry logic

**Auto-Documentation (Job 13):**
- Metadata catalog
- Lineage tracking
- API documentation
- Usage analytics

**Portfolio Management (Job 24):**
- Monthly GitHub commits
- Version control
- Change history

## 8. Key Design Patterns

### Data Engineering Patterns

**Medallion Architecture:**
- Bronze: Raw, immutable data
- Silver: Cleansed, conformed data
- Gold: Business-ready aggregates

**SCD Type 2:**
- Historical tracking
- Effective dates
- Current flag

**Change Data Capture:**
- Real-time streaming
- MERGE operations
- Watermark tracking

**Incremental Processing:**
- Timestamp-based
- Checkpoint management
- Idempotent operations

### ML Engineering Patterns

**Feature Store:**
- Centralized features
- Point-in-time correctness
- Online/offline serving

**Experiment Tracking:**
- Reproducible runs
- Parameter tuning
- Model comparison

**Model Monitoring:**
- Prediction drift
- Data drift
- Performance metrics

### Architecture Patterns

**Modularity:**
- Reusable components
- Clear interfaces
- Separation of concerns

**Scalability:**
- Auto-scaling compute
- Partitioning strategies
- Optimization techniques

**Reliability:**
- Error handling
- Retry logic
- Data quality checks

## 9. Performance & Optimization

### Query Optimization

**Z-Ordering:**
- Co-location of related data
- Faster query performance
- Reduced I/O

**Partitioning:**
- Date-based partitions
- Pruning optimization
- Balanced partition sizes

**Caching:**
- Delta cache
- Spark cache
- Result caching

### Compute Optimization

**Auto-Scaling:**
- Dynamic resource allocation
- Cost optimization
- Performance balance

**Cluster Policies:**
- Standardized configurations
- Resource limits
- Security settings

## 10. Security & Governance

### Access Control

**Unity Catalog:**
- Catalog-level permissions
- Schema-level permissions
- Table-level permissions
- Column-level masking

**Row-Level Security:**
- Dynamic filtering
- User-based access
- Group-based access

### Audit & Compliance

**Audit Logs:**
- User activity tracking
- Data access logs
- Change tracking

**Data Lineage:**
- Source to consumption
- Transformation tracking
- Impact analysis

**Secrets Management:**
- Credential encryption
- Scope-based access
- Integration with external vaults

## Success Metrics

| Metric | Achievement |
|--------|-------------|
| **Data Latency** | 5-8 min (incremental), 20-25 min (full) |
| **Data Quality** | 500+ automated tests |
| **ML Models** | 5 production models, 100% monitored |
| **Dashboards** | 13 interactive dashboards |
| **Cost** | $0 (Free Edition) |
| **Uptime** | 99%+ job success rate |

## Getting Started

### Prerequisites
- Databricks Community Edition account
- GitHub account (for CI/CD)
- Basic understanding of Python and SQL

### Quick Start

1. **Setup Environment**
   ```
   Configure environment variables
   Set Unity Catalog paths
   ```

2. **Generate Data**
   ```
   Run data generator
   Create synthetic data
   ```

3. **Run Full Load**
   ```
   Execute pipeline orchestrator
   Monitor job execution
   ```

4. **Verify Results**
   ```
   Check dashboards
   Query Genie Spaces
   Review ML metrics
   ```

### Configuration

**Environment Variables:**
```
SKILLAIPPATH_ENV=dev|uat|prod
SKILLAIPPATH_CATALOG=sap
```

**Catalog Structure:**
```
catalog.{env}_bronze.*    # Raw staging
catalog.{env}_silver.*    # Transformed
catalog.{env}_gold.*      # Business marts
```

## Additional Resources

**Documentation:**
- Canvas_Guide.md - Canvas platform foundation
- Assets.csv / Assets.tsv - Complete asset inventory
- Architecture diagrams - Visual references

**External Links:**
- Databricks Documentation
- Delta Lake Guide
- MLflow Documentation
- DBT Best Practices

---

**Version 1.0** - Production Release  
**Platform:** Databricks Free Edition  
**Architecture:** Medallion + ML + BI  
**Coverage:** End-to-end data platform
