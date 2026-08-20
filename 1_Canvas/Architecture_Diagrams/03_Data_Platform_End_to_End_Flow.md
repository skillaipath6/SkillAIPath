# End-to-End Data Flow Architecture
## Source → Bronze → Silver → Gold → Analytics | Complete Data Journey

Comprehensive view of data flow across the entire SkillAIPath platform from external sources through all transformation layers to end-user consumption.

---

## Complete Data Flow

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                       MEDALLLION ARCHITECTURE DATA FLOW                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│  EXTERNAL DATA SOURCES                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Google Sheets │  │   REST APIs   │  │ File Uploads │  │ External DBs   │ │
│  │ Training Data │  │   External    │  │ CSV/JSON/    │  │ MySQL/Postgres │ │
│  │               │  │   Services    │  │ Parquet      │  │                │ │
│  └───────┬───────┘  └───────┬───────┘  └──────┬───────┘  └────────┬───────┘ │
│          │                  │                   │                   │         │
└──────────┼──────────────────┼───────────────────┼───────────────────┼─────────┘
           │                  │                   │                   │
           ↓                  ↓                   ↓                   ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ DATA INGESTION LAYER                                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  ┌────────────┐  │
│  │ 3_Data_         │  │  AutoLoader  │  │   Lakehouse    │  │    CDC     │  │
│  │ Integrations    │  │  Incremental │  │   Federation   │  │  Pipeline  │  │
│  │ Sync Scripts    │  │  Ingest      │  │ Query Pushdown │  │  Real-Time │  │
│  └────────┬────────┘  └──────┬───────┘  └────────┬───────┘  └─────┬──────┘  │
│           │                  │                     │                │         │
└───────────┼──────────────────┼─────────────────────┼────────────────┼─────────┘
            │                  │                     │                │
            └──────────────────┴─────────────────────┴────────────────┘
                                        │
                                        ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│  BRONZE LAYER (Raw Data - Immutable Source of Truth)                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────┐    ┌────────────────────────────┐  │
│  │   Bronze Tables                      │    │   /Volumes/raw_data/       │  │
│  │   skillaipath_main.bronze.*          │    │   File Storage (Parquet)   │  │
│  │                                      │    │                            │  │
│  │   • Raw data as ingested             │    │   • Landing zone files     │  │
│  │   • Audit columns (ingested_at)      │    │   • Checkpoint metadata    │  │
│  │   • No transformations               │    │   • Error quarantine       │  │
│  └──────────────┬───────────────────────┘    └────────────────────────────┘  │
│                 │                                                             │
└─────────────────┼─────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ ⚪ SILVER LAYER (Cleaned & Validated Data)                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────┐       ┌───────────────────────┐                    │
│  │  Data Validation     │       │  Data Cleaning        │                    │
│  ├──────────────────────┤  ───→ ├───────────────────────┤                    │
│  │ • Schema enforcement │       │ • Deduplication       │                    │
│  │ • Data quality checks│       │ • Type conversions    │                    │
│  │ • Null handling      │       │ • Standardization     │                    │
│  └──────────┬───────────┘       └───────────┬───────────┘                    │
│             │                               │                                 │
│             └───────────────┬───────────────┘                                 │
│                             ↓                                                 │
│            ┌────────────────────────────────────┐                             │
│            │  Silver Tables                     │                             │
│            │  skillaipath_main.silver.*         │                             │
│            │                                    │                             │
│            │  • Cleaned & validated data        │                             │
│            │  • Conformed data types            │                             │
│            │  • Business keys established       │                             │
│            └────────────────┬───────────────────┘                             │
│                             │                                                 │
└─────────────────────────────┼───────────────────────────────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│  GOLD LAYER (Analytics-Ready Star Schema)                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────┐  ┌────────────────────┐  ┌──────────────────────┐ │
│  │ Dimension Tables     │  │   Fact Tables      │  │  Aggregated Views    │ │
│  ├──────────────────────┤  ├────────────────────┤  ├──────────────────────┤ │
│  │ • dim_customer       │  │ • fact_sales       │  │ • customer_360       │ │
│  │ • dim_product        │  │ • fact_orders      │  │ • product_perf       │ │
│  │ • dim_date           │  │ • fact_inventory   │  │ • sales_summary      │ │
│  │ • dim_location       │  │ • fact_returns     │  │ • monthly_metrics    │ │
│  │                      │  │                    │  │                      │ │
│  │ ✓ SCD Type 2         │  │ ✓ Foreign keys     │  │ ✓ Pre-aggregated     │ │
│  │ ✓ Surrogate keys     │  │ ✓ Metrics          │  │ ✓ KPIs ready         │ │
│  └──────────┬───────────┘  └─────────┬──────────┘  └──────────┬───────────┘ │
│             │                        │                         │             │
│             └────────────────────────┴─────────────────────────┘             │
│                                      │                                        │
└──────────────────────────────────────┼────────────────────────────────────────┘
                                       │
                                       ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ DATA CONSUMPTION LAYER                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │  Lakeview     │  │  ML Models  │  │  Databricks  │  │   AI Agents    │   │
│  │  Dashboards   │  │  Feature    │  │  Apps        │  │   LangChain    │   │
│  ├───────────────┤  ├─────────────┤  ├──────────────┤  ├────────────────┤   │
│  │ • Executive   │  │ • Feature   │  │ • Streamlit  │  │ • RAG Pipeline │   │
│  │   Reporting   │  │   Store     │  │ • FastAPI    │  │ • Function     │   │
│  │ • Operational │  │ • Training  │  │ • Gradio     │  │   Calling      │   │
│  │   Analytics   │  │ • Serving   │  │              │  │                │   │
│  └───────────────┘  └─────────────┘  └──────────────┘  └────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │   Delta Sharing (External Partners)                          │            │
│  │   ─ Share tables with external organizations                 │            │
│  │   ─ Secure data exchange without data movement               │            │
│  └──────────────────────────────────────────────────────────────┘            │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

DATA FLOW KEY:
  │  Vertical flow (transformation pipeline)
  →  Horizontal flow (processing step)
  ↓  Layer transition (bronze → silver → gold → consumption)
```

---

## Data Layer Summary

| Layer      | Purpose               | Retention | Volume | Freshness   | Format          |
|------------|-----------------------|-----------|--------|-------------|-----------------|
| **Bronze** | Immutable raw data    | 7 years   | 100%   | Real-time   | Delta/Parquet   |
| **Silver** | Cleaned & validated   | 5 years   | 80%    | < 1 hour    | Delta           |
| **Gold**   | Analytics aggregates  | 3 years   | 20%    | < 15 min    | Delta           |

---

## Data Processing Patterns

### Ingestion Patterns
* **Batch**: Scheduled full/incremental loads (daily, hourly)
* **Streaming**: Real-time CDC from databases
* **Micro-batch**: AutoLoader for files (trigger: availableNow)
* **Federation**: Query-time access to external databases

### Transformation Patterns
* **Bronze → Silver**: Validation, cleaning, deduplication
* **Silver → Gold**: Star schema modeling, aggregations
* **Gold → Consumption**: Materialized views, feature engineering

### Quality Gates
* **Bronze**: Schema validation, file integrity
* **Silver**: Business rule validation, referential integrity
* **Gold**: KPI consistency, metric accuracy

---

## Key Data Principles

### 1. **Immutable Bronze**
* Raw data is never modified or deleted
* Audit trail preserved for compliance
* Enables reprocessing and debugging

### 2. **Validated Silver**
* All data quality checks enforced
* Schema evolution managed
* Business keys established

### 3. **Optimized Gold**
* Query performance optimized (Z-ordering, partitioning)
* Star schema for BI tools
* Pre-aggregated for fast analytics

### 4. **Secure Consumption**
* Row-level security (Unity Catalog)
* Column masking for PII
* Audit logging for compliance

---

**Version**: 2.0  
**Last Updated**: 2026-08-04  
**Status**: Production Data Flow Active (ASCII Format)
