# BI Production Stack Architecture
## Lakeview Dashboards | Genie Spaces | SQL Endpoints

Production BI platform with self-service analytics and AI-powered query interfaces.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   BI PRODUCTION STACK ARCHITECTURE                          │
└──────────────────────────────────────────────────────────────────────────────┘

        Gold Layer (Business Metrics)
                   │
                   ↓
        ┌──────────────────────┐
        │   SQL Warehouse      │
        │  (Compute Layer)     │
        └──────────┬───────────┘
                   │
       ┌───────────┼───────────┐
       │           │            │
       ↓           ↓            ↓
  ┌────────┐  ┌────────┐  ┌────────┐
  │Lakeview│  │  Genie │  │  SQL   │
  │Dashboard│  │ Spaces │  │ Editor │
  └────┬────┘  └────┬────┘  └────┬────┘
       │           │            │
       └───────────┼───────────┘
                   ↓
        ┌──────────────────────┐
        │   Business Users    │
        │  (Self-Service)     │
        └──────────────────────┘
```

Components: Lakeview dashboards, Genie Spaces for NL queries, SQL endpoints
Access control: Unity Catalog row-level security
Refresh: Scheduled via Databricks Jobs
Module: 4_Business_Intelligence/2_BI_Production
