# Canvas Platform
## Foundation Layer for SkillAIPath

### Architecture

```
Canvas Platform (Foundation for Everything)
        |
        +--- Setup Bootstrap (Config, data generation, reset)
        |
        +--- Orchestration (Full/incremental pipeline orchestration)
        |
        +--- Industry Patterns (40 production patterns)
        |
        +--- OnboardingLibrary (Asset inventory and documentation)
        |
        +--- AI Agent Coordination (10 autonomous agents)
        |
        +--- Architecture Diagrams (20 ASCII diagrams)
        |
        +--- Data Platform + AI Platform + BI (Built on Canvas)
```

### Folder Structure

```
1_Canvas/
├── 0_Setup_Bootstrap/           Config, data generation, reset
├── 2_Orchestration/             Full/incremental pipeline orchestration
├── 6_Industry_Patterns/         40 production patterns (AI Gateway, CDC, etc)
├── OnboardingLibrary/           Asset inventory and dashboard guide
├── [Moved to 5_Growth_Accelerator/6_AI_Agent_Coordination]     10 autonomous agents
└── Architecture_Diagrams/       20 ASCII diagrams (system -> component -> detail)
```

### Components

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| Setup | Bootstrap catalogs, generate test data | 1_config, 2_data_generator |
| Orchestration | Run full/incremental pipelines | 12_Start_FullLoad, 13_Start_IncrementalLoad |
| Industry Patterns | 40 production patterns (CDC, AI Gateway, etc) | 40 pattern implementations |
| OnboardingLibrary | Asset inventory and dashboard documentation | Assets.csv, SkillAIPath_Guide.md |
| AI Agents | 10 autonomous agents, parallel execution | AGENT_COORDINATION_SYSTEM.md |
| Diagrams | 20 ASCII architecture diagrams | System/Component/Detail levels |

### Assets and Documentation

**Location:** /Shared/dev/SkillAIPath/1_Canvas/OnboardingLibrary/

| File | Purpose |
|------|---------|
| Assets.csv | Complete asset inventory: 23 jobs, 13 dashboards, 4 Genie spaces, 3 catalogs, 4 apps |
| SkillAIPath_Guide.md | Comprehensive platform documentation (in root folder) |

**Dashboard Organization:**
- All 13 dashboards in single folder: /Shared/dev/SkillAIPath/Dashboards/
- Naming convention: [Category] - [Descriptive Name]
- Categories: Executive, Sales, Operations, Customer, Platform, ML, Demo
- 8 business intelligence dashboards + 5 ML model monitoring dashboards
- 100% ML model coverage: Churn, Recommendations, Forecasting, Next Purchase, Training Pipeline

### Quick Start

| Step | Action | File | Time |
|------|--------|------|------|
| 1 | Configure environment | 0_Setup_Bootstrap/1_config | 1min |
| 2 | Generate test data | 0_Setup_Bootstrap/2_data_generator | 5min |
| 3 | Run full load pipeline | 2_Orchestration/Data_Platform/12_Start_FullLoad | 20min |
| 4 | Explore industry patterns | 6_Industry_Patterns/ | - |
| 5 | Launch autonomous agents | ../5_Growth_Accelerator/6_AI_Agent_Coordination/ | 3min |

### Orchestration Patterns

```
FULL LOAD (20-25 min):
Bronze (validate) -> Dimensions (9) -> Facts (3) -> Gold (4) -> Quality

INCREMENTAL LOAD (5-8 min):
Bronze (CDC) -> Dimensions (SCD2) -> Facts (MERGE) -> Gold (refresh) -> Quality
```

### AI Agent Coordination

```
           Orchestrator (You)
                  |
       +----------+----------+
       |          |          |
   Agent1     Agent2     Agent10
  (branch1)  (branch2)  (branch10)
       |          |          |
   [WORK]     [WORK]     [WORK]
       |          |          |
   Quality    Quality    Quality
    Gates      Gates      Gates
       |          |          |
    Create     Create     Create
      PR         PR         PR
       |          |          |
       +----------+----------+
                  |
         You Approve & Merge
```

**Result:** 4 days manual work -> 2-4 hours autonomous

### Industry Patterns (40 Implementations)

| Pattern Category | Count | Examples |
|------------------|-------|----------|
| AI Gateway | 8 | Routing, fallback, rate limits |
| CDC/Streaming | 6 | Auto CDC, Kafka, Kinesis |
| Federation | 5 | PostgreSQL, MySQL, Snowflake |
| Governance | 7 | Row filters, column masks, ABAC |
| Delta Sharing | 4 | Share creation, recipient setup |
| Optimization | 6 | Liquid clustering, Z-order |
| Security | 4 | Secrets, tokens, encryption |

### Architecture Diagrams (20 Total)

```
Level 1: System Overview (1)
  └─ 00_Canvas_System_Overview.md

Level 2: Major Components (8)
  ├─ 01_DevOps_Production_Architecture.md
  ├─ 02_Setup_Bootstrap_Architecture.md
  ├─ 03_Orchestration_Architecture.md
  ├─ 04_Industry_Patterns_Architecture.md
  ├─ Data_Integrations_Flow.md
  ├─ AI_Agent_Templates_Architecture.md
  ├─ App_Templates_Stack.md
  └─ Execution_Training_System.md

Level 3: Sub-Components (5)
  ├─ 05_Agent_Blueprints_Catalog.md
  ├─ 06_App_Templates_Catalog.md
  ├─ 07_Industry_Patterns_Catalog.md
  ├─ 08_Training_Task_Patterns_Architecture.md
  └─ 09_Training_Sessions_Architecture.md

Level 4: Flows (3)
  ├─ 10_End_to_End_Data_Flow.md
  ├─ 11_DevOps_CICD_Pipeline.md
  └─ 12_AI_Gateway_Integration_Architecture.md
```

### Configuration Pattern

```python
class Config:
    # Environment (dev/uat/prod)
    ENVIRONMENT = os.getenv("SKILLAIPPATH_ENV", "dev")
    
    # Unity Catalog
    CATALOG = os.getenv("SKILLAIPPATH_CATALOG", "sap")
    SCHEMA_BRONZE = f"{CATALOG}.{ENVIRONMENT}_bronze"
    SCHEMA_SILVER = f"{CATALOG}.{ENVIRONMENT}_silver"
    SCHEMA_GOLD = f"{CATALOG}.{ENVIRONMENT}_gold"
    
    # Override via environment variables
```

### Data Flow

```
External Sources (APIs, Files, DBs)
         |
         v
  Bronze (Raw ingestion)
         |
         v
  Silver (Dims + Facts, SCD2)
         |
         v
   Gold (Business marts)
         |
         v
  Consumption (BI, Genie, Apps)
```

### When to Use Canvas Components

| Need | Use This | Skip This |
|------|----------|-----------|
| Bootstrap new environment | 0_Setup_Bootstrap/ | Manual setup |
| Run pipelines | 2_Orchestration/ | Manual notebook execution |
| Production patterns | 6_Industry_Patterns/ | Reinventing patterns |
| Multi-branch coordination | ../5_Growth_Accelerator/6_AI_Agent_Coordination/ | Manual Genie prompts |
| Understand architecture | Architecture_Diagrams/ | Guessing structure |

### Dashboard Migration Guide

**Current State:**
Dashboards are scattered across various workspace locations.

**Target State:**
All dashboards in /Shared/dev/SkillAIPath/Dashboards/ with standardized names.

**Migration Steps:**

1. Rename Dashboard
   - Open dashboard
   - Click "..." menu -> Rename
   - Use new name: [Category] - [Descriptive Name]

2. Move Dashboard
   - Click "..." menu -> Move
   - Navigate to /Shared/dev/SkillAIPath/Dashboards/
   - Confirm move

3. Verify
   - Check dashboard in new location
   - Test functionality
   - Update bookmarks

### ML Dashboard Configuration

**Common Widget Types:**
- Model Performance Metrics (Accuracy, Precision, Recall, F1, RMSE, MAE, MAPE)
- Prediction Analysis (Distribution, confidence scores, error analysis)
- Model Drift Monitoring (Data drift, prediction drift, feature distribution)
- Training Metadata (Run history, hyperparameters, duration, versions)
- Business Impact (Predictions vs actuals, ROI, A/B test results)

**Data Sources:**
- MLflow tracking tables (experiments, runs, metrics)
- Feature store tables
- Prediction tables (batch and real-time)

**Configuration Steps:**
1. Identify MLflow experiment IDs
2. Locate prediction output tables
3. Create base queries for metrics
4. Build visualization widgets
5. Set refresh schedules
6. Add alert thresholds

### ML Model to Job Mapping

**Training Data Pipeline**
- Job: 14_Weekly_Training_Data_Extraction
- Schedule: Weekly
- Dashboards: ML - Churn Prediction, ML - Training Pipeline

**Churn Prediction**
- Job: 15_Weekly_Churn_Prediction
- Dashboard: ML - Churn Prediction Performance

**Product Recommendations**
- Job: 16_Weekly_Product_Recommendation
- Dashboard: ML - Product Recommendation Engine

**Demand Forecasting**
- Job: 17_Weekly_Demand_Forecasting
- Dashboard: ML - Demand Forecasting Analytics

**Next Purchase Prediction**
- Job: 18_Weekly_Next_Purchase_Prediction
- Dashboard: ML - Next Purchase Prediction

### Success Metrics

| Metric | Before Canvas | With Canvas |
|--------|---------------|-------------|
| Setup time | 2-3 days | 5 minutes |
| Pipeline execution | Manual, 1-2 hours | Automated, 20 min |
| Multi-branch coordination | 4 days sequential | 2-4 hours parallel |
| Pattern reuse | 0 (start from scratch) | 40 production patterns |
| Onboarding | Weeks (learn codebase) | Hours (read diagrams) |

### Next Steps

**Immediate Actions:**
1. Complete dashboard migration to production folder
2. Verify all dashboards renamed and moved
3. Update external links and bookmarks

**ML Dashboard Configuration:**
1. Identify MLflow experiment IDs
2. Locate prediction output tables
3. Create base queries for metrics
4. Build visualization widgets
5. Configure auto-refresh schedules
6. Add alert thresholds

**Ongoing Maintenance:**
1. Monitor dashboard performance
2. Update queries as data sources change
3. Add new dashboards following naming convention
4. Regular review of ML model metrics
5. Keep documentation current

### Support

**Dashboard Issues:**
- Check query performance
- Verify data source availability
- Review refresh schedules
- Validate user permissions

**ML Dashboard Issues:**
- Verify MLflow experiment connectivity
- Check prediction table availability
- Validate feature store access
- Review model registry permissions

### Reference

**Key Files:**
- Assets.csv - Complete asset inventory
- SkillAIPath_Guide.md - Overall platform guide (in root)
- This file - Canvas-specific documentation

**Key Locations:**
- Dashboard Folder: /Shared/dev/SkillAIPath/Dashboards/
- Documentation: /Shared/dev/SkillAIPath/1_Canvas/OnboardingLibrary/
- Industry Patterns: /Shared/dev/SkillAIPath/1_Canvas/6_Industry_Patterns/

---

END OF CANVAS GUIDE
