# SKILLAIPATH - COMPLETE JOB TECHNICAL ARCHITECTURE

**Last Updated:** August 20, 2026  
**Version:** 1.0 - Production Architecture  
**Status:** PRODUCTION READY  

---


**23 Production Jobs | End-to-End Data & AI Platform**

---

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                    SKILLAIPATH PRODUCTION JOB ARCHITECTURE (23 JOBS)                                  ║
║                                   TECHNICAL FLOW DIAGRAM                                               ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ SETUP & FOUNDATION (Sequential)                                                                    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│    Job 01: DevOps Setup (On-Demand)                                                                   │
│           • Unity Catalog init                                                                         │
│           • Workspace config                                                                           │
│           • Permissions setup                                                                          │
│              │                                                                                          │
│              ▼                                                                                          │
│    Job 02: EduFin Core Analytics (On-Demand)                                                           │
│           • Demo catalog (sap_dev)                                                                     │
│           • Business analytics baseline                                                                │
│              │                                                                                          │
└──────────────┼────────────────────────────────────────────────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│   BRONZE LAYER - INGESTION (All Parallel)                                                            │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐            │
│   │ Data Generator   │  │   REST APIs      │  │ Google Sheets    │  │  Google Docs     │            │
│   │ External DBs     │  │   OAuth Auth     │  │ Drive API Sync   │  │  Text Extract    │            │
│   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘            │
│            │                     │                      │                      │                      │
│            └─────────────────────┴──────────────────────┴──────────────────────┘                      │
│                                         │                                                              │
│                                         ▼                                                              │
│                      ┌────────────────────────────────────────┐                                       │
│                      │  Job 03: Lakehouse Full Load (Daily)   │                                       │
│                      │  • 6 bronze tables (stg_*)             │                                       │
│                      │  • Full refresh                         │ ◄── PARALLEL                          │
│                      │  • Schema evolution                     │                                       │
│                      └────────────────────────────────────────┘                                       │
│                                         │                                                              │
│                      ┌────────────────────────────────────────┐                                       │
│                      │  Job 04: Lakehouse Incremental (Daily) │                                       │
│                      │  • Watermarking                        │ ◄── PARALLEL                          │
│                      │  • AutoLoader CDC                      │                                       │
│                      │  • < 5 min latency                     │                                       │
│                      └────────────────────────────────────────┘                                       │
│                                         │                                                              │
│ Output: skillaipath_main.bronze.* (6 tables)                                                      │
└────────────────────────────────────────┼──────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  ⚪ SILVER LAYER - TRANSFORMATION (All Parallel Engines)                                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────┐           │
│   │  ENGINE 1: LAKEHOUSE + DBT                                                            │           │
│   │  ┌──────────────────────────────────────────────────────────────────────────────────┐  │           │
│   │  │  Job 05: DBT Full Transformation (Daily)                                       │  │ ◄─ PARALLEL│
│   │  │  • 13 tables: 9 dims (SCD Type 2) + 3 facts + 1 bridge                       │  │           │
│   │  │  • 500+ DBT tests                                                             │  │           │
│   │  │  • Surrogate keys, FK relationships                                           │  │           │
│   │  └──────────────────────────────────────────────────────────────────────────────────┘  │           │
│   │  ┌──────────────────────────────────────────────────────────────────────────────────┐  │           │
│   │  │  Job 06: DBT Incremental (Daily)                                              │  │ ◄─ PARALLEL│
│   │  │  • CDC via MERGE                                                              │  │           │
│   │  │  • Watermarking (last_updated_at)                                             │  │           │
│   │  │  • SCD Type 2 (valid_from/to, is_current)                                     │  │           │
│   │  └──────────────────────────────────────────────────────────────────────────────────┘  │           │
│   └──────────────────────────────────────────────────────────────────────────────────────────────┘           │
│                                                                                                        │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────┐           │
│   │  ENGINE 2: DLT STREAMING                                                              │           │
│   │  ┌──────────────────────────────────────────────────────────────────────────────────┐  │           │
│   │  │  Job 08: Streaming CDC (Daily)                                                │  │ ◄─ PARALLEL│
│   │  │  • Real-time change capture                                                   │  │           │
│   │  │  • < 5 min latency                                                            │  │           │
│   │  │  • Auto-scaling compute                                                       │  │           │
│   │  └──────────────────────────────────────────────────────────────────────────────────┘  │           │
│   │  ┌──────────────────────────────────────────────────────────────────────────────────┐  │           │
│   │  │  Job 09: Bronze-Silver DLT (Daily)                                            │  │ ◄─ PARALLEL│
│   │  │  • Expectations (inline quality checks)                                       │  │           │
│   │  │  • Materialized views                                                         │  │           │
│   │  │  • Auto-recovery                                                              │  │           │
│   │  └──────────────────────────────────────────────────────────────────────────────────┘  │           │
│   └──────────────────────────────────────────────────────────────────────────────────────────────┘           │
│                                                                                                        │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────┐           │
│   │  ENGINE 3: LAKEBASE SYNC                                                              │           │
│   │  ┌──────────────────────────────────────────────────────────────────────────────────┐  │           │
│   │  │  Job 21: Lakebase Sync (Daily)                                                │  │ ◄─ PARALLEL│
│   │  │  • OLTP → OLAP (Postgres → Delta)                                            │  │           │
│   │  │  • Incremental MERGE                                                          │  │           │
│   │  │  • Target: sap_dev catalog                                                    │  │           │
│   │  └──────────────────────────────────────────────────────────────────────────────────┘  │           │
│   └──────────────────────────────────────────────────────────────────────────────────────────────┘           │
│                                                                                                        │
│ Output: skillaipath_main.silver.* (13 tables)                                                     │
│ Validation: Schema checks, deduplication, null handling, referential integrity                    │
│ Optimization: Z-ordering, Vacuum, Statistics refresh, Liquid clustering                          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│   GOLD LAYER - ANALYTICS-READY MARTS                                                                 │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│ Star Schema Views & Business Catalog Tables (skillaipath_main.gold.*)                            │
│                                                                                                        │
│   ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐                         │
│   │ Customer Analytics  │  │ Product Analytics   │  │ Marketing Analytics │                         │
│   │ • mart_customer_360 │  │ • mart_product_perf │  │ • mart_rfm_analysis │                         │
│   │ • RFM scores        │  │ • Sales velocity    │  │ • Segmentation      │                         │
│   │ • Lifetime value    │  │ • ABC class         │  │ • Cohort analysis   │                         │
│   └─────────────────────┘  └─────────────────────┘  └─────────────────────┘                         │
│                                                                                                        │
│   ┌─────────────────────┐  ┌─────────────────────┐                                                   │
│   │ ML Feature Store    │  │ Operational Views   │                                                   │
│   │ • user_session_ml   │  │ • sales_summary     │                                                   │
│   │ • Behavior features │  │ • inventory_snap    │                                                   │
│   └─────────────────────┘  └─────────────────────┘                                                   │
│                                         │                                                              │
└────────────────────────────────────────┼──────────────────────────────────────────────────────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
┌──────────────────────────────────────────────┐  ┌──────────────────────────────────────────────┐
│ AI PLATFORM (Jobs 10-18)                 │  │ BI PLATFORM (Jobs 07, 20 + Assets)       │
├──────────────────────────────────────────────┤  ├──────────────────────────────────────────────┤
│                                              │  │                                              │
│  Job 10: Knowledge Retrieval (Daily)         │  │  Job 07: Genie Spaces (On-Demand)           │
│         • RAG pipeline                       │  │         • Automated space creation           │
│         • Vector embeddings        ◄─PARALLEL│  │         • Seed conversations      ◄─PARALLEL │
│                                              │  │                                              │
│  Job 11: Ecommerce Intelligence (Daily)      │  │  Job 20: App Deployment (Weekly)             │
│         • Business metrics         ◄─PARALLEL│  │         • 7 Streamlit apps        ◄─PARALLEL │
│                                              │  │         • Real-time monitoring               │
│  Job 12: Customer 360 (Daily)                │  │         • Predictive analytics               │
│         • Unified customer view    ◄─PARALLEL│  │                                              │
│                                              │  │  ────────────────────────────────            │
│  Job 13: Auto Documentation (Daily)          │  │                                              │
│         • Code → docs automation   ◄─PARALLEL│  │ Dashboards (10 certified)                │
│                                              │  │    • Executive KPIs                          │
│  Job 14: Training Data Extraction (Weekly)   │  │    • Operational metrics                     │
│         • Feature engineering               │  │    • Customer insights                       │
│         • ML-ready datasets                  │  │    • Sales analytics                         │
│              │                               │  │                                              │
│              └────────────┐                  │  │ Apps (7 production)                      │
│                           ▼                  │  │    • PR Reviewer                             │
│         ┌─────────────────────────────────┐ │  │    • Content Studio                          │
│         │  ML TRAINING (All Parallel)     │ │  │    • Team Operations                         │
│         ├─────────────────────────────────┤ │  │    • Real-Time Monitor                       │
│         │ Job 15: Churn Prediction        │ │  │    • Executive Reports                       │
│         │ Job 16: Product Recommendation  │ │  │    • Supply Chain API                        │
│         │ Job 17: Demand Forecasting      │ │  │    • Gold Analytics Dashboard                │
│         │ Job 18: Next Purchase Prediction│ │  │                                              │
│         │         (Weekly)                │ │  │ Genie Spaces (2 active)                  │
│         └─────────────────────────────────┘ │  │    • Sales Analytics Q&A                     │
│                                              │  │    • Inventory Intelligence                  │
│ Output:                                  │  │                                              │
│    • 4 MLflow models                         │  │ VDP Flows (6 pipelines)                  │
│    • Inference endpoints                     │  │    • Visual data transformations             │
│    • Feature tables                          │  │                                              │
│                                              │  │ Cost Tracking & Monitoring               │
│ AI Agents (19 blueprints)               │  │    • Usage analytics                         │
│    • Code review, testing, ops               │  │    • Performance metrics                     │
│    • Learning & workflow automation          │  │    • Cluster utilization                     │
└──────────────────────────────────────────────┘  └──────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════════════════════════════════ ORCHESTRATION & MAINTENANCE

   Job 19: Incremental Refresh (Daily)     ── Keeps all layers current (Bronze → Silver → Gold)
   Job 22: Master SkillAI (Weekly)         ── Full end-to-end orchestration (all 23 jobs)
   Job 23: GitHub AutoCommit (Monthly)     ── Portfolio sync & version control

══════════════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## TECHNICAL SUMMARY

| Layer | Jobs | Schedule | Parallelism | Output |
|-------|------|----------|-------------|--------|
| **Setup** | 01-02 | On-Demand | Sequential | Catalogs, Workspace |
| **Bronze** | 03-04 | Daily | Parallel | 6 tables |
| **Silver** | 05-06, 08-09, 21 | Daily | All Parallel (5 jobs) | 13 tables |
| **Gold** | Derived from Silver | - | - | 4+ marts |
| **AI** | 10-18 | Daily/Weekly | Mostly Parallel (9 jobs) | 4 models, RAG, docs |
| **BI** | 07, 20 | On-Demand/Weekly | Parallel | 10 dashboards, 7 apps |
| **Orchestration** | 19, 22-23 | Daily/Weekly/Monthly | - | Platform health |

**Total:** 23 production jobs

---

## DEPENDENCY RULES

**Sequential:**
- Job 01 → Job 02 → Jobs 03-04
- Job 14 → Jobs 15-18 (ML training depends on feature extraction)

**All Parallel:**
- Bronze: Jobs 03-04 run together
- Silver: Jobs 05-06, 08-09, 21 run together after Bronze completes
- AI Analytics: Jobs 10-13 run together after Silver completes
- ML Training: Jobs 15-18 run together after Job 14 completes
- BI: Job 07, Job 20, Dashboards all run together after Gold is ready

**Independent:**
- Job 19: Runs daily to refresh all layers incrementally
- Job 22: Weekly master orchestrator (runs all jobs)
- Job 23: Monthly GitHub sync (independent of data flow)

---

**Platform:** Databricks FREE Edition  
**Cost:** $0/month  
**Status:** PRODUCTION READY  
**Last Updated:** August 16, 2026
