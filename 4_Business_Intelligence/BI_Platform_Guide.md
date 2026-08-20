# Business Intelligence Platform Guide
## 8-Subsystem Monitoring | Lakeview Dashboards | Genie Spaces

Comprehensive BI platform with monitoring, dashboards, and live applications.

## Architecture

* [Platform Observability Complete](Architecture_Diagrams/Platform_Observability_Complete.md)
* [BI Production Stack](Architecture_Diagrams/BI_Production_Stack.md)
* [Live Apps Architecture](Architecture_Diagrams/Live_Apps_Architecture.md)

## Components

### 1_Platform_Observability
8 monitoring subsystems:
1. cost_tracking
2. custom_metrics
3. data_quality
4. lakehouse_monitoring
5. ml_monitoring
6. performance_monitoring
7. Alert Management
8. runbooks (4 incident response guides)

Live Apps:
* Intelligence Hub (platform metrics)
* Agents Dashboard (agent monitoring)

### 2_BI_Production
Lakeview dashboards, Genie Spaces, SQL endpoints

### 3_Live_Apps
Real-time Streamlit applications with 30-second refresh

Module: 4_Business_Intelligence
Last Updated: January 2025
