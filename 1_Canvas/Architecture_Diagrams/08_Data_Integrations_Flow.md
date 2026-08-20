# Data Integrations Flow Architecture
## Google Sheets | Genie Spaces | Dashboard Builders | Refresh Jobs

Orchestrates external data connections and automated dashboard refresh workflows.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA INTEGRATIONS ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SOURCES                                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Google Sheets]             [Genie Spaces]                              │
│   Business Data               AI Data Rooms                              │
│         │                          │                                     │
└─────────┬───────────────────────────┬──────────────────────────────┘
         │                                  │
         ↓                                  ↓
┌─────────┴──────────────────────────────────────────────────────┴────────┐
│                     INTEGRATION LAYER                                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  google_sheet_sync (OAuth 2.0)    genie_space_setup (Config)            │
│           │                                  │                          │
│           ↓                                  ↓                          │
│  curated_view_builder (SQL)       dashboard_builder (Lakeview API)      │
│                                                                          │
└───────────────┬──────────────────────────────────────────────────────────┘
                ↓
┌───────────────┼──────────────────────────────────────────────────────────┐
│                      UNITY CATALOG STORAGE                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  BRONZE (Raw Data) ──> SILVER (Curated Views) ──> GOLD (Dashboards)    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                 ↑
┌─────────────────────────────────┴────────────────────────────────────────┐
│                      ORCHESTRATION                                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  quick_validate (30 min setup)    schedule_refresh_job (Auto refresh)   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Google Sheets Sync
* Bi-directional sync between Sheets and Delta tables
* OAuth 2.0 authentication
* Hourly scheduled refresh
* Incremental updates only

### 2. Genie Space Setup
* Configure AI-powered data rooms
* Natural language query interface
* Unity Catalog table selection
* Business glossary definitions

### 3. Curated View Builder
* SQL view generation
* Business logic and transformations
* Metric calculations (profit, margin)
* Date windowing and aggregations

### 4. Dashboard Builder
* Programmatic Lakeview dashboard creation
* REST API integration
* Widget configuration (counters, charts, tables)
* Auto-deployment

### 5. Quick Validate
* 30-minute end-to-end validation
* Tests all integrations
* Verifies Bronze/Silver/Gold layers
* Confirms Genie Space queries

### 6. Schedule Refresh Job
* Hourly/daily/phase-based automation
* Databricks Jobs scheduling
* Error handling and retry logic

Integration time: 30 minutes (quick_validate)
Module: 1_Canvas/3_Data_Integrations
Last Updated: January 2025
