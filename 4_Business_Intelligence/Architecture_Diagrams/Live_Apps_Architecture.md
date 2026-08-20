# Live Apps Architecture
## Intelligence Hub | Agents Dashboard | Real-Time Data Refresh

Streamlit-based live applications with real-time dashboards and monitoring.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      LIVE APPS ARCHITECTURE                                │
└──────────────────────────────────────────────────────────────────────────────┘

     Databricks Jobs (Data Pipeline)
                │
                ↓
     ┌────────────────────────────┐
     │ Unity Catalog Delta Tables  │
     └─────────────┬───────────────┘
                │
                ↓
     ┌────────────────────────────┐
     │   Streamlit Runtime       │
     │ (Databricks Apps)        │
     └───────────┬────────────────┘
                │
      ┌─────────┼─────────┐
      │          │          │
      ↓          ↓          ↓
┌───────────┐  ┌──────────┐
│Intelligence│  │  Agents  │
│    Hub     │  │Dashboard│
│ (Platform │  │ (Agent  │
│  Metrics) │  │Monitor)│
└────┬───────┘  └───┬──────┘
     │             │
     └──────┬──────┘
            │
            ↓
    Auto Refresh (30s)
```

Apps: Intelligence Hub (platform observability), Agents Dashboard (agent performance)
Runtime: Streamlit on Databricks Apps
Refresh: Real-time with 30-second intervals
Module: 4_Business_Intelligence/3_Live_Apps
