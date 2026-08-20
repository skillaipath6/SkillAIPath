# Retail Operations Apps - Lakebase Setup

## Overview

This job initializes and maintains the **retail-ops-apps** Lakebase Postgres database that powers three live retail applications.

## Supported Applications

1. **01_Inventory_Command_Center** - Real-time inventory monitoring with approval workflow
2. **02_Demand_Forecasting_Dashboard** - Predictive analytics for demand planning 
3. **03_Dynamic_Pricing_API** - Dynamic pricing engine

## Lakebase Configuration

| Property | Value |
|----------|-------|
| **Project** | retail-ops-apps |
| **Branch** | production |
| **Endpoint** | primary |
| **Host** | ep-rough-mud-d8fhvjws.database.us-east-2.cloud.databricks.com |
| **Database** | databricks_postgres |
| **Port** | 5432 |

## Database Schema

### Table: `reorder_approvals`

Stores reorder requests from the Inventory Command Center app.

```sql
CREATE TABLE reorder_approvals (
 id SERIAL PRIMARY KEY,
 product_sk INTEGER NOT NULL,
 product_name VARCHAR(255) NOT NULL,
 warehouse_sk INTEGER NOT NULL,
 warehouse_name VARCHAR(255) NOT NULL,
 recommended_qty INTEGER NOT NULL,
 current_stock INTEGER NOT NULL,
 urgency VARCHAR(50) NOT NULL,
 status VARCHAR(50) NOT NULL DEFAULT 'pending',
 notes TEXT,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 approved_at TIMESTAMP,
 approved_by VARCHAR(255)
);
```

**Indexes:**
- `idx_reorder_approvals_status` - Filter by approval status
- `idx_reorder_approvals_created_at` - Time-based queries
- `idx_reorder_approvals_product_warehouse` - Product/warehouse lookups

## Job Configuration

**Job ID:** 893066158608868 
**Job Name:** Lakebase_Retail_Ops_Apps 
**Type:** One-time setup / On-demand maintenance

### Task: Setup_Retail_Ops_Database

- **Notebook:** `/Users/skillaipath15@gmail.com/Lakebase_Retail_Ops_Setup`
- **Purpose:** Initialize schema, create tables, insert sample data
- **Runtime:** ~1-2 minutes

## Setup Steps

### 1. Lakebase Project Created ```bash
Project: retail-ops-apps
Branch: production (auto-created)
Endpoint: primary (auto-created, 1 CU, scale-to-zero enabled)
```

### 2. Run Setup Job
```bash
# Trigger the job
databricks jobs run-now 893066158608868
```

### 3. Verify Setup
The notebook will output:
- Table created
- Indexes created
- Sample data inserted
- Statistics (record count)

### 4. Deploy Apps
Once the job completes, the apps can connect to the Lakebase database.

## Maintenance

### Re-run Setup (Idempotent)
The setup is **idempotent** - safe to run multiple times:
- Tables use `CREATE TABLE IF NOT EXISTS`
- Sample data only inserted if table is empty
- Indexes use `CREATE INDEX IF NOT EXISTS`

### Manual Access
```python
from databricks.sdk import WorkspaceClient
import psycopg2

w = WorkspaceClient()
creds = w.postgres.generate_database_credential(
 endpoint="projects/retail-ops-apps/branches/production/endpoints/primary"
)

conn = psycopg2.connect(
 host="ep-rough-mud-d8fhvjws.database.us-east-2.cloud.databricks.com",
 port=5432,
 database="databricks_postgres",
 user=w.current_user.me().user_name,
 password=creds.token,
 sslmode="require"
)
```

## File Locations

```
/Shared/dev/SkillAIPath/
├── 1_Canvas/3_Production_Jobs/
│ └── 24_Lakebase_Retail_Ops_Apps.json # Job configuration
│
├── 4_Business_Intelligence/3_Live_Apps/
│ ├── 01_Inventory_Command_Center/
│ ├── 02_Demand_Forecasting_Dashboard/
│ ├── 03_Dynamic_Pricing_API/
│ └── _shared/
│ ├── config.py
│ ├── lakebase_config.py # Connection settings
│ └── db_manager.py # DB helpers
│
└── /Users/skillaipath15@gmail.com/
 └── Lakebase_Retail_Ops_Setup.ipynb # Setup notebook
```

## Related Resources

- **Job:** [Lakebase_Retail_Ops_Apps](#job-893066158608868)
- **Notebook:** [Lakebase_Retail_Ops_Setup](#notebook-957576300622273)
- **Apps Directory:** `/Shared/dev/SkillAIPath/4_Business_Intelligence/3_Live_Apps/`

## Tags

- `category`: lakebase
- `environment`: production
- `app_tier`: retail_operations

---

**Created:** 2026-08-16 
**Status:** Ready to run 
**Next Step:** Run job 893066158608868 to initialize database
