# SkillAIPath Monitoring & Observability Architecture

**Technical Design Document**

---

## System Overview

The SkillAIPath Monitoring & Observability platform is an enterprise-grade, automated monitoring system built on Databricks that provides comprehensive visibility into data quality, performance, and costs across the SkillAIPath data platform.

### Design Principles

1. **Automation-First**: Fully automated execution with minimal manual intervention
2. **Observability**: Complete visibility into all aspects of the platform
3. **Scalability**: Designed to scale from 18 to 100+ tables
4. **Modularity**: Easy to add/remove/modify monitoring components
5. **Resilience**: Built-in retry logic and error handling
6. **Unity Catalog Native**: Leverages UC for governance and lineage

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER │
│ │
│ ┌─────────────────────┐ ┌─────────────────────┐ │
│ │ Lakeview Dashboard │ │ Email Alerts │ │
│ │ (Real-time) │ │ (On Failure) │ │
│ └──────────┬──────────┘ └──────────┬──────────┘ │
└─────────────┼──────────────────────────┼────────────────────────────┘
 │ │
 │ │
┌─────────────▼──────────────────────────▼────────────────────────────┐
│ ORCHESTRATION LAYER │
│ │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Master Orchestrator (orchestrator.py) │ │
│ │ • Parallel execution engine │ │
│ │ • Sequential dependency management │ │
│ │ • Retry logic with exponential backoff │ │
│ │ • Error handling and alerting │ │
│ │ • Results persistence │ │
│ └───────────────┬────────────────────────────────────────────┘ │
└──────────────────┼───────────────────────────────────────────────────┘
 │
 │
┌──────────────────▼───────────────────────────────────────────────────┐
│ EXECUTION LAYER │
│ │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │Data Quality │ │Performance │ │Cost Tracking │ │
│ │Monitoring │ │Monitoring │ │& Analysis │ │
│ │ │ │ │ │ │ │
│ │• Bronze checks│ │• Delta opts │ │• DBU usage │ │
│ │• Silver checks│ │• Bottlenecks │ │• Storage cost│ │
│ │• Gold checks │ │• History │ │• Audit logs │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
│ │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ML Monitoring │ │Lakehouse │ │Custom Metrics│ │
│ │(Sequential) │ │Monitoring │ │(Extensible) │ │
│ │ │ │(Sequential) │ │ │ │
│ │• Drift detect│ │• UC monitors │ │• Business KPIs│ │
│ │• Analysis │ │• Config mgmt │ │• Custom checks│ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
└──────────────────┬───────────────────────────────────────────────────┘
 │
 │
┌──────────────────▼───────────────────────────────────────────────────┐
│ DATA LAYER │
│ (Unity Catalog) │
│ │
│ sap_dev.monitoring schema: │
│ ├─ orchestration_runs (run tracking) │
│ ├─ data_quality_results (quality metrics) │
│ ├─ performance_metrics (optimization data) │
│ └─ cost_tracking_results (cost analysis) │
│ │
│ sap_dev layers (monitored): │
│ ├─ bronze (3 staging tables) │
│ ├─ silver (12 fact + dimension tables) │
│ └─ gold (3 mart tables) │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Configuration Management (`config.py`)

**Purpose**: Central configuration for all environments and table mappings

**Key Features**:
* Multi-environment support (dev/uat/prod)
* Dynamic table resolution
* Threshold management
* Credential handling (via environment variables)

**Structure**:
```python
class SkillAIPathConfig:
 ENVIRONMENT: str # dev/uat/prod
 CATALOG: str # sap_{env}
 BRONZE_SCHEMA: str
 SILVER_SCHEMA: str
 GOLD_SCHEMA: str
 MONITORING_SCHEMA: str
 
 # Table registry (18 tables)
 BRONZE_TABLES: Dict[str, str]
 SILVER_TABLES: Dict[str, str]
 GOLD_TABLES: Dict[str, str]
 
 # Thresholds
 QUALITY_THRESHOLD: float = 0.8
 OPTIMIZE_THRESHOLD: int = 500
 
 # Methods
 get_table_path(table_key: str) -> str
 validate_config() -> bool
```

### 2. Master Orchestrator (`orchestrator.py`)

**Purpose**: Execution engine that coordinates all monitoring workflows

**Architecture Pattern**: Parallel + Sequential Hybrid

**Execution Flow**:
```
1. Initialize
 ├─ Load configuration
 ├─ Setup logging
 └─ Create execution plan

2. Execute Phase 1 (Parallel)
 ├─ data_quality/
 ├─ performance_monitoring/
 └─ cost_tracking/
 └─ (All run simultaneously)

3. Execute Phase 2 (Sequential)
 ├─ ml_monitoring/ (waits for previous)
 └─ lakehouse_monitoring/ (waits for ml_monitoring)

4. Post-Processing
 ├─ Collect results
 ├─ Persist to Unity Catalog
 ├─ Send alerts
 └─ Generate summary
```

**Key Classes**:

```python
@dataclass
class ScriptExecution:
 script_path: str
 status: str # pending/running/success/failed/skipped
 start_time: datetime
 end_time: datetime
 duration_seconds: float
 error_message: str
 retry_count: int
 results: Dict

class MonitoringOrchestrator:
 def __init__(self, run_id: str)
 def execute_script(self, script_path: str) -> ScriptExecution
 def execute_category_sequential(self, category: str) -> List[ScriptExecution]
 def execute_category_parallel(self, categories: Dict) -> List[ScriptExecution]
 def persist_results(self) -> None
 def send_alerts(self) -> None
 def run(self) -> None
```

**Retry Logic**:
* Max retries: 2
* Backoff: Exponential (5s, 10s, 20s)
* Retry on: Transient failures only
* No retry on: Permission errors, table not found

### 3. Monitoring Scripts

#### Data Quality Monitoring

**Scripts**:
* `data_quality/data_quality_checks.sql` (10KB)

**Checks Performed**:
1. **Null Checks**: Critical columns null percentage
2. **Duplicate Checks**: Primary key duplicates
3. **Referential Integrity**: Foreign key validation
4. **Business Rules**: Domain-specific validation
5. **Freshness**: Data recency checks
6. **Cross-Layer Reconciliation**: Bronze → Silver → Gold consistency

**Output Schema**:
```sql
CREATE TABLE sap_dev.monitoring.data_quality_results (
 check_id STRING,
 check_timestamp TIMESTAMP,
 check_date DATE,
 table_name STRING,
 layer STRING,
 total_rows BIGINT,
 quality_score_pct DECIMAL(5,2),
 null_count BIGINT,
 duplicate_count BIGINT,
 invalid_count BIGINT,
 status STRING, -- 'pass'/'warning'/'critical'
 details MAP<STRING, STRING>
);
```

#### Performance Monitoring

**Scripts**:
* `performance_monitoring/delta_optimization_metrics.sql` (6KB)
* `performance_monitoring/bottleneck_detection.sql`
* `performance_monitoring/delta_table_history.sql`

**Metrics Collected**:
1. **Small File Detection**: Files < 128MB
2. **Table Growth**: Size trends over time
3. **Query Performance**: Slow queries (>5 min)
4. **Optimization Recommendations**: OPTIMIZE/VACUUM candidates

**Output Schema**:
```sql
CREATE TABLE sap_dev.monitoring.performance_metrics (
 metric_id STRING,
 metric_timestamp TIMESTAMP,
 metric_date DATE,
 table_name STRING,
 layer STRING,
 file_count BIGINT,
 avg_file_size_mb DECIMAL(10,2),
 small_file_count BIGINT,
 recommendation STRING, -- 'optimize_urgent'/'vacuum_needed'/etc
 details MAP<STRING, STRING>
);
```

#### Cost Tracking

**Scripts**:
* `cost_tracking/cost_attribution.sql` (4KB)
* `cost_tracking/audit_logs_analysis.sql`

**Metrics Collected**:
1. **DBU Usage**: By workspace/cluster/job
2. **Query Costs**: Expensive queries identification
3. **Storage Costs**: Table size × storage rate
4. **Waste Detection**: Idle clusters, unused tables

**Output Schema**:
```sql
CREATE TABLE sap_dev.monitoring.cost_tracking_results (
 cost_id STRING,
 cost_timestamp TIMESTAMP,
 cost_date DATE,
 cost_type STRING, -- 'dbu'/'storage'/'query'
 dbu_usage DECIMAL(18,2),
 estimated_cost_usd DECIMAL(18,2),
 resource_id STRING,
 resource_name STRING,
 optimization_flag STRING,
 details MAP<STRING, STRING>
);
```

### 4. Results Storage (Unity Catalog)

**Schema**: `sap_dev.monitoring`

**Design Principles**:
* Date partitioning for performance
* MAP columns for extensibility
* Idempotent writes (INSERT overwrite patterns)
* Time travel enabled (Delta)

**Data Retention**:
* Raw results: 90 days
* Aggregated metrics: 1 year
* Audit trail: 7 years (compliance)

### 5. Scheduling (Databricks Jobs)

**Job Configurations**:

| Job | Schedule | Compute | Duration | Retries |
|-----|----------|---------|----------|---------|
| Daily Monitoring | 6 AM daily | 2-node i3.xlarge | ~20 min | 2 |
| Weekly Analysis | Mon 8 AM | 4-node i3.xlarge | ~45 min | 2 |
| On-Demand | Manual | 2-node i3.xlarge | ~15 min | 0 |

**Cluster Configuration**:
```json
{
 "spark_version": "14.3.x-scala2.12",
 "node_type_id": "i3.xlarge",
 "autoscale": {
 "min_workers": 2,
 "max_workers": 4
 },
 "spark_conf": {
 "spark.databricks.delta.preview.enabled": "true",
 "spark.sql.adaptive.enabled": "true"
 }
}
```

### 6. Alerting System

**Channels**:
1. **Email**: On failure (immediate)
2. **Dashboard**: Real-time status
3. **Logs**: Detailed CloudWatch integration (future)

**Alert Severity**:
* **CRITICAL**: Core monitoring failed, immediate action
* **HIGH**: Multiple failures, investigate within 2 hours
* **MEDIUM**: Single failure, investigate within 24 hours
* **LOW**: Informational, no action needed

---

## Data Flow

### Standard Execution Flow

```
1. Job Trigger (Scheduled or Manual)
 └─> Databricks Job starts

2. Orchestrator Initialization
 └─> Load config.py
 └─> Validate environment
 └─> Create run_id (UUID)

3. Parallel Execution (Phase 1)
 ├─> data_quality_checks.sql
 │ └─> Query Bronze/Silver/Gold tables
 │ └─> Calculate metrics
 │ └─> Return results
 │
 ├─> delta_optimization_metrics.sql
 │ └─> DESCRIBE DETAIL on all tables
 │ └─> Calculate file statistics
 │ └─> Generate recommendations
 │
 └─> cost_attribution.sql
 └─> Query system.access.audit
 └─> Query system.query.history
 └─> Calculate costs

4. Sequential Execution (Phase 2)
 └─> ml_monitoring (if enabled)
 └─> lakehouse_monitoring (if enabled)

5. Results Collection
 └─> Aggregate all ScriptExecution objects
 └─> Calculate summary statistics

6. Persistence
 └─> Write to orchestration_runs
 └─> Write to data_quality_results
 └─> Write to performance_metrics
 └─> Write to cost_tracking_results

7. Alerting
 └─> Check for failures
 └─> Send emails if needed
 └─> Log summary

8. Dashboard Refresh
 └─> Lakeview queries monitoring tables
 └─> Real-time updates appear
```

---

## Security & Permissions

### Required Permissions

**Service Account**: `service-sap-monitoring`

**Unity Catalog**:
```sql
-- Catalog level
GRANT USAGE ON CATALOG sap_dev TO `service-sap-monitoring`;

-- Schema level
GRANT USAGE, SELECT ON SCHEMA sap_dev.bronze TO `service-sap-monitoring`;
GRANT USAGE, SELECT ON SCHEMA sap_dev.silver TO `service-sap-monitoring`;
GRANT USAGE, SELECT ON SCHEMA sap_dev.gold TO `service-sap-monitoring`;
GRANT ALL PRIVILEGES ON SCHEMA sap_dev.monitoring TO `service-sap-monitoring`;

-- System tables
GRANT SELECT ON system.access.audit TO `service-sap-monitoring`;
GRANT SELECT ON system.query.history TO `service-sap-monitoring`;
```

**Workspace**:
* Can Run jobs
* Can access Databricks SQL
* Can read workspace files

---

## Scalability Considerations

### Current Scale
* **Tables Monitored**: 18
* **Scripts**: 6
* **Daily Executions**: ~20 minutes
* **Data Volume**: ~100GB monitored

### Designed For
* **Tables**: Up to 500
* **Scripts**: Up to 50
* **Execution Time**: Up to 2 hours
* **Data Volume**: Up to 10TB

### Scaling Strategies

**Horizontal Scaling**:
* Add more parallel categories
* Increase cluster workers (2 → 8 → 16)

**Vertical Scaling**:
* Larger node types (i3.xlarge → i3.2xlarge)
* More memory for aggregations

**Optimization**:
* Sample large tables (1% representative sample)
* Incremental monitoring (only changed data)
* Caching frequently accessed tables

---

## Extension Points

### Adding New Monitoring Category

1. Create folder: `monitoring_observability/{new_category}/`
2. Add scripts: `{new_category}/monitor_script.sql`
3. Update orchestrator.py:
 ```python
 'new_category': {
 'parallel': True,
 'scripts': ['new_category/monitor_script.sql'],
 'priority': 1
 }
 ```
4. (Optional) Add results table in monitoring schema
5. Update dashboard to include new metrics

### Adding New Table to Monitor

1. Update config.py:
 ```python
 SILVER_TABLES = {
 # ... existing ...
 'new_table': 'new_table_name'
 }
 ```
2. Existing scripts automatically include it
3. No orchestrator changes needed

---

## Technology Stack

* **Orchestration**: Python 3.10
* **Data Processing**: Databricks SQL, PySpark
* **Storage**: Unity Catalog (Delta Lake)
* **Scheduling**: Databricks Jobs
* **Visualization**: Lakeview Dashboards
* **SDK**: databricks-sdk 0.18+
* **Version Control**: Git

---

## Future Enhancements

1. **Real-time Monitoring**: Streaming alerts via Kafka
2. **ML-Powered Anomaly Detection**: Auto-detect unusual patterns
3. **Cost Forecasting**: Predict future costs based on trends
4. **Auto-Remediation**: Automatic OPTIMIZE/VACUUM execution
5. **Multi-Region**: Support for cross-region monitoring
6. **API Access**: REST API for programmatic access to metrics

---

**Document Owner**: SkillAIPath Platform Team 
**Last Updated**: 2026-07-11 
**Next Review**: 2026-10-11
