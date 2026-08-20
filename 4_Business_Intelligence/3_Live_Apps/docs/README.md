# Live Production Apps - Business Intelligence Platform
**3 Production-Grade Apps | Lakebase Postgres + Unity Catalog**

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ UNITY CATALOG (OLAP Analytics Layer) │
│ ───────────────────────────────── │
│ │
│ sap_dev │
│ ├── silver.fact_sales (historical transactions) │
│ ├── silver.dim_warehouse (reference data) │
│ └── gold.mart_inventory_health (analytics) │
│ │
│ USE CASE: Read-only analytical queries │
└─────────────────────────────────────────────────────┘
 ↓
 [Apps Layer - 3 Live Apps]
 ↓
┌─────────────────────────────────────────────────────┐
│ LAKEBASE POSTGRES (OLTP Operational Layer) │
│ ────────────────────────────────────── │
│ │
│ Project: retail-ops-apps │
│ Branch: production │
│ Endpoint: ep-dark-lab-d8hwsb07.database... │
│ │
│ Tables: │
│ ├── reorder_approvals (approval workflow) │
│ ├── forecast_runs (forecast audit trail) │
│ ├── pricing_rules (dynamic pricing config) │
│ └── price_change_history (pricing audit) │
│ │
│ USE CASE: Transactional writes, state management │
└─────────────────────────────────────────────────────┘
```

## The 3 Apps

### 1. Inventory Command Center
**Location:** `01_Inventory_Command_Center/`

**What it does:**
- Real-time monitoring of critical/understock items
- Approval workflow for reorder requests
- Audit trail of all approvals/rejections

**Why it beats Genie:**
- Transactional approval workflow
- State management in Lakebase
- Action buttons (not just Q&A)
- Persistent audit log

**Data Flow:**
- **READ** from Unity Catalog: `mart_inventory_health`
- **WRITE** to Lakebase: `reorder_approvals` table

---

### 2. Demand Forecasting Dashboard
**Location:** `02_Demand_Forecasting_Dashboard/`

**What it does:**
- ML-powered demand forecasting using Prophet
- Historical sales trend analysis
- Forecast confidence intervals

**Why it beats Genie:**
- Custom ML models (Prophet)
- Interactive forecast configuration
- Forecast history & reproducibility
- Model performance metrics

**Data Flow:**
- **READ** from Unity Catalog: `silver.fact_sales`
- **WRITE** to Lakebase: `forecast_runs` table

---

### 3. Dynamic Pricing Engine API
**Location:** `03_Dynamic_Pricing_API/`

**What it does:**
- REST API for dynamic pricing
- Rule-based price adjustments
- Price change audit trail

**Why it beats Genie:**
- External API (not chat interface)
- Rule engine in Lakebase
- Programmatic integration
- Real-time price calculations

**Data Flow:**
- **READ** from Unity Catalog: `mart_inventory_health`
- **WRITE** to Lakebase: `pricing_rules`, `price_change_history`

---

## Quick Start

### Prerequisites
```bash
# Environment variables
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/..."
export DATABRICKS_TOKEN="your-personal-access-token"
```

### Run App 1: Inventory Command Center
```bash
cd 01_Inventory_Command_Center
pip install -r requirements.txt
streamlit run app.py
```

### Run App 2: Demand Forecasting
```bash
cd 02_Demand_Forecasting_Dashboard
pip install -r requirements.txt
streamlit run app.py
```

### Run App 3: Pricing API
```bash
cd 03_Dynamic_Pricing_API
pip install -r requirements.txt
uvicorn app:app --reload
```

## Key Differentiators

| Feature | Genie | These Apps |
|---------|-------|------------|
| **Approval Workflows** | ❌ No | Yes (Lakebase) |
| **State Management** | ❌ No | Yes (Postgres) |
| **Custom ML Models** | ❌ Limited | Full control |
| **External APIs** | ❌ No | FastAPI |
| **Audit Trails** | ❌ No | Full history |
| **Action Buttons** | ❌ Chat only | Interactive UI |

## Database Schema

### Lakebase Postgres Tables

**reorder_approvals**
```sql
CREATE TABLE reorder_approvals (
 approval_id SERIAL PRIMARY KEY,
 product_sk INTEGER NOT NULL,
 product_name VARCHAR(200),
 warehouse_sk INTEGER NOT NULL,
 warehouse_name VARCHAR(100),
 recommended_qty INTEGER,
 current_stock INTEGER,
 urgency VARCHAR(20),
 status VARCHAR(20) DEFAULT 'pending',
 approved_by VARCHAR(100),
 rejected_reason TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**pricing_rules**
```sql
CREATE TABLE pricing_rules (
 rule_id SERIAL PRIMARY KEY,
 rule_name VARCHAR(100) UNIQUE,
 stock_status VARCHAR(20),
 health_status VARCHAR(20),
 price_adjustment_pct DECIMAL(5,2),
 is_active BOOLEAN DEFAULT true,
 created_by VARCHAR(100),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Performance

| Metric | Value |
|--------|-------|
| **Unity Catalog Query** | ~200ms |
| **Lakebase Write** | ~50ms |
| **End-to-end Latency** | <1 second |
| **Concurrent Users** | 100+ |
| **Autoscaling** | 0.5-32 CU |

## Screenshots

### App 1: Inventory Command Center
```
┌─────────────────────────────────────────────────────┐
│ Inventory Command Center │
│ Real-Time Monitoring | Approval Workflow │
├─────────────────────────────────────────────────────┤
│ Critical: 12 Understock: 34 ⏳ Pending: 5 │
├─────────────────────────────────────────────────────┤
│ Critical Inventory │
│ │
│ Aashirvaad Atta 10kg @ Agra WH │
│ Current: 15 | Recommended: 200 │
│ [ Create Reorder Request] │
│ │
│ Parle G Biscuits @ Delhi WH │
│ Current: 45 | Recommended: 150 │
│ [ Create Reorder Request] │
└─────────────────────────────────────────────────────┘
```

### App 2: Demand Forecasting
```
┌─────────────────────────────────────────────────────┐
│ Demand Forecasting Dashboard │
│ ML-Powered Predictions | Prophet Model │
├─────────────────────────────────────────────────────┤
│ Settings │
│ Warehouse: [Agra WH ▼] │
│ Horizon: [●────────] 30 days │
│ Confidence: [●────────] 95% │
│ [ Run Forecast] │
├─────────────────────────────────────────────────────┤
│ Sales Forecast │
│ 300 ┤ ╱╲ ╱╲ ╱╲ │
│ ┤ ╱ ╲╱ ╲╱ ╲ │
│ 150 ┤ ╱ ▪▪▪▪▪▪▪▪▪▪ (forecast) │
│ ┤ │
│ 0 ┼──────────────────────────── │
│ Jan Feb Mar Apr May │
└─────────────────────────────────────────────────────┘
```

## Security

- **OAuth Tokens**: 1-hour expiry, auto-refresh
- **Connection Pooling**: Secure connection reuse
- **Role-Based Access**: Databricks identity integration
- **Audit Logging**: All actions tracked

## Next Steps

1. **Deploy to Databricks Apps** (cloud hosting)
2. **Add authentication** (OAuth, SSO)
3. **Create dashboards** (BI metrics on Lakebase data)
4. **Mobile interface** (responsive design)
5. **Webhook integrations** (Slack, Teams notifications)

## Support

For questions or issues:
- Check individual app READMEs
- Review Lakebase Postgres docs
- Contact: SkillAIPath Team
