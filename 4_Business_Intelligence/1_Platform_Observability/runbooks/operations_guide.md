# SkillAIPath Monitoring & Observability Operations Guide

**Version**: 1.0.0 
**Last Updated**: 2026-07-11 
**Maintained By**: SkillAIPath Platform Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Daily Operations](#daily-operations)
4. [Scheduled Jobs](#scheduled-jobs)
5. [Monitoring Results](#monitoring-results)
6. [Troubleshooting](#troubleshooting)
7. [Alert Response](#alert-response)
8. [Adding New Monitors](#adding-new-monitors)
9. [Escalation Procedures](#escalation-procedures)

---

## Overview

The SkillAIPath Monitoring & Observability platform provides automated monitoring across 6 key categories:

| Category | Purpose | Frequency |
|----------|---------|-----------|
| **Data Quality** | Bronze/Silver/Gold layer health checks | Daily |
| **Performance Monitoring** | Delta optimization, bottleneck detection | Daily |
| **Cost Tracking** | DBU usage, storage costs, expensive queries | Daily |
| **ML Monitoring** | Model drift detection (when ML deployed) | Weekly |
| **Lakehouse Monitoring** | UC quality monitors (when configured) | Weekly |
| **Custom Metrics** | Business-specific KPIs | On-demand |

### Key Components

* **Configuration**: `config.py` - Central configuration for all environments
* **Orchestrator**: `orchestrator.py` - Master execution engine
* **Monitoring Schema**: `sap_dev.monitoring` - Results storage in Unity Catalog
* **Dashboard**: Lakeview dashboard for real-time visibility
* **Jobs**: 3 scheduled Databricks Jobs (daily, phase-based, on-demand)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ MONITORING ORCHESTRATOR │
│ (orchestrator.py) │
└────────────┬────────────────────────────────────────────────────┘
 │
 ├─── PARALLEL EXECUTION ───┐
 │ │
 ┌───────▼────────┐ ┌───────▼────────┐
 │ Data Quality │ │ Performance │
 │ Monitoring │ │ Monitoring │
 └───────┬────────┘ └───────┬────────┘
 │ │
 ┌───────▼────────┐ ┌───────▼────────┐
 │ Cost Tracking │ │ ML Monitoring │
 │ & Analysis │ │ (Sequential) │
 └───────┬────────┘ └───────┬────────┘
 │ │
 └──────────┬───────────────┘
 │
 ┌──────────▼───────────┐
 │ RESULTS PERSISTENCE │
 │ sap_dev. │
 │ monitoring schema │
 └──────────┬───────────┘
 │
 ┌──────────▼───────────┐
 │ ALERTING SYSTEM │
 │ (Email/Slack/Logs) │
 └──────────────────────┘
```

### Data Flow

1. **Orchestrator starts** → Reads `config.py` for environment and table configuration
2. **Parallel execution** → Data Quality, Performance, Cost scripts run simultaneously
3. **Sequential execution** → ML/Lakehouse monitors run in order (dependencies)
4. **Results capture** → All outputs written to UC monitoring tables
5. **Alert evaluation** → Failures trigger email notifications
6. **Dashboard refresh** → Lakeview dashboard shows latest status

---

## Daily Operations

### Morning Health Check (5 minutes)

**Time**: 9:00 AM daily 
**Priority**: HIGH

1. **Check Dashboard**
 * Open [SkillAIPath Monitoring Dashboard](#)
 * Verify last run status (should be GREEN)
 * Check success rate (should be >95%)

2. **Review Failures**
 * If any RED status, check "Recent Failed Runs" table
 * Note failed script names and error messages

3. **Validate Key Metrics**
 * Data Quality Score: Should be >90% for all layers
 * Performance Issues: Note any tables with >1000 small files
 * Cost Anomalies: Check for unexpected DBU spikes

### Response Actions

| Status | Action | Priority |
|--------|--------|----------|
| All GREEN | No action needed | LOW |
| 1-2 failures | Investigate within 2 hours | MEDIUM |
| 3+ failures | Immediate investigation | HIGH |
| Critical table failure | Page on-call engineer | CRITICAL |

---

## ⏰ Scheduled Jobs

### 1. Daily Monitoring Job

**Job Name**: `SkillAIPath_Daily_Monitoring` 
**Schedule**: Daily at 6:00 AM UTC 
**Duration**: ~15-20 minutes 
**Compute**: 2-node i3.xlarge cluster

**What it does**:
* Data quality checks across Bronze/Silver/Gold
* Delta table optimization metrics
* Cost attribution and DBU tracking
* Audit log analysis

**Expected Results**:
* 6 monitoring scripts executed
* Results in `sap_dev.monitoring.*` tables
* Email notification on failure only

**How to run manually**:
```bash
# Via Databricks CLI
databricks jobs run-now --job-name SkillAIPath_Daily_Monitoring

# Via UI
Workflows → SkillAIPath_Daily_Monitoring → Run Now
```

### 2. Weekly Deep Analysis Job

**Job Name**: `SkillAIPath_Weekly_Deep_Analysis` 
**Schedule**: Every Monday at 8:00 AM UTC 
**Duration**: ~30-45 minutes 
**Compute**: 4-node i3.xlarge cluster

**What it does**:
* Comprehensive optimization recommendations
* Cost trend analysis (past 30 days)
* Performance bottleneck deep dive
* Table history and operations audit

**Expected Results**:
* Detailed analysis reports
* Optimization recommendations
* Cost forecasting data
* Email notification with summary

### 3. On-Demand Health Check

**Job Name**: `SkillAIPath_OnDemand_HealthCheck` 
**Schedule**: Manual trigger 
**Duration**: ~10-15 minutes 
**Compute**: 2-node i3.xlarge cluster

**When to use**:
* After major data pipeline changes
* When investigating data quality issues
* Before production deployments
* After schema migrations

**How to run**:
```bash
databricks jobs run-now --job-name SkillAIPath_OnDemand_HealthCheck
```

---

## Monitoring Results

All monitoring results are stored in Unity Catalog:

### Schema: `sap_dev.monitoring`

#### 1. `orchestration_runs`
Tracks each orchestration execution:
```sql
SELECT * FROM sap_dev.monitoring.orchestration_runs
WHERE run_date >= CURRENT_DATE() - 7
ORDER BY run_timestamp DESC;
```

**Key Columns**:
* `run_id` - Unique execution identifier
* `status` - success / partial_failure / failed
* `scripts_executed` - Total scripts run
* `scripts_success` - Successfully completed
* `scripts_failed` - Failed scripts
* `duration_seconds` - Total execution time

#### 2. `data_quality_results`
Data quality metrics by table and layer:
```sql
SELECT table_name, layer, quality_score_pct, status
FROM sap_dev.monitoring.data_quality_results
WHERE check_date >= CURRENT_DATE() - 7
ORDER BY quality_score_pct ASC;
```

**Alert Thresholds**:
* Quality Score < 80%: WARNING
* Quality Score < 60%: CRITICAL

#### 3. `performance_metrics`
Performance and optimization metrics:
```sql
SELECT table_name, small_file_count, recommendation
FROM sap_dev.monitoring.performance_metrics
WHERE metric_date >= CURRENT_DATE() - 7
 AND small_file_count > 100
ORDER BY small_file_count DESC;
```

**Alert Thresholds**:
* Small files > 500: OPTIMIZE recommended
* Small files > 1000: OPTIMIZE urgent

#### 4. `cost_tracking_results`
Cost and usage tracking:
```sql
SELECT cost_type, SUM(estimated_cost_usd) as total_cost
FROM sap_dev.monitoring.cost_tracking_results
WHERE cost_date >= CURRENT_DATE() - 30
GROUP BY cost_type
ORDER BY total_cost DESC;
```

---

## Troubleshooting

### Common Issues

#### Issue: Orchestrator fails to start

**Symptoms**:
* Job fails immediately
* Error: "Module not found: config"

**Resolution**:
1. Verify `config.py` exists at correct path
2. Check Python environment has databricks-sdk installed
3. Validate Unity Catalog permissions

**Fix**:
```bash
# Check config file
ls -la /Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/1_Monitoring_Observability/config.py

# Test config import
python -c "import sys; sys.path.insert(0, '/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/1_Monitoring_Observability'); from config import config; print(config.CATALOG)"
```

#### Issue: SQL scripts fail with table not found

**Symptoms**:
* Script execution fails
* Error: "Table or view not found: sap_dev.silver.fact_sales"

**Resolution**:
1. Verify table exists in Unity Catalog
2. Check user has SELECT permissions
3. Validate catalog/schema configuration

**Fix**:
```sql
-- Check table existence
SHOW TABLES IN sap_dev.silver;

-- Check permissions
SHOW GRANTS ON TABLE sap_dev.silver.fact_sales;
```

#### Issue: Results not written to monitoring tables

**Symptoms**:
* Orchestration completes but no results
* Monitoring tables empty or stale

**Resolution**:
1. Check INSERT permissions on monitoring schema
2. Verify orchestrator completes without errors
3. Check for transaction rollbacks

**Fix**:
```sql
-- Check permissions
SHOW GRANTS ON SCHEMA sap_dev.monitoring;

-- Verify latest results
SELECT MAX(check_timestamp) FROM sap_dev.monitoring.data_quality_results;
```

#### Issue: High cost alerts

**Symptoms**:
* Unexpected DBU usage spikes
* Cost tracking shows anomalies

**Investigation Steps**:
1. Query audit logs for long-running queries
2. Check for unoptimized tables
3. Review cluster autoscaling settings

**Query**:
```sql
SELECT query_id, user_name, execution_duration/1000.0 as duration_sec
FROM system.query.history
WHERE query_start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP())
 AND execution_duration > 300000 -- 5 minutes
ORDER BY execution_duration DESC;
```

---

## Alert Response

### Email Alert Received

**Subject**: "SkillAIPath Monitoring Job Failed"

**Immediate Actions** (5 minutes):

1. **Open Dashboard**
 * Check overall health status
 * Identify which category failed

2. **Check Run Details**
 * Query orchestration_runs table for latest run
 * Note error_message

3. **Assess Impact**
 * CRITICAL: Core data quality checks failed
 * HIGH: Multiple scripts failed
 * MEDIUM: Single script failed
 * LOW: Retry succeeded

### Response Procedures

#### Critical Path Failure (Bronze/Silver/Gold quality checks)

**Priority**: IMMEDIATE (respond within 15 minutes)

1. Run on-demand health check
2. If failure persists, check source data pipelines
3. Notify data engineering team
4. Create incident ticket

#### Performance/Cost Monitoring Failure

**Priority**: HIGH (respond within 2 hours)

1. Review error message
2. Check system.query.history for issues
3. Retry monitoring job
4. If success, document as transient failure

#### One-off Script Failure

**Priority**: MEDIUM (respond within 24 hours)

1. Review script logs
2. Check for recent code changes
3. Create bug ticket
4. Script will retry automatically

---

## ➕ Adding New Monitors

### Step 1: Create Monitoring Script

Choose script type (SQL or Python):

**SQL Script Template** (`custom_metrics/new_monitor.sql`):
```sql
-- Databricks notebook source
-- MAGIC %md
-- MAGIC # New Custom Monitor
-- MAGIC **Purpose**: [Describe what this monitors]
-- MAGIC **Frequency**: [Daily/Weekly/On-demand]

-- COMMAND ----------

-- Your monitoring query here
SELECT 
 CURRENT_TIMESTAMP() as check_timestamp,
 'your_metric_name' as metric_name,
 COUNT(*) as metric_value,
 'your_table' as table_name
FROM your_catalog.your_schema.your_table
WHERE your_conditions;

-- COMMAND ----------

-- Write results (optional)
-- INSERT INTO sap_dev.monitoring.custom_metrics
-- SELECT * FROM results_above;
```

**Python Script Template** (`custom_metrics/new_monitor.py`):
```python
"""New Custom Monitor

Purpose: [Describe what this monitors]
Frequency: [Daily/Weekly/On-demand]
"""

import sys
sys.path.insert(0, "/Workspace/Shared/dev/SkillAIPath/4_Business_Intelligence/1_Monitoring_Observability")

from config import config
from pyspark.sql import SparkSession
import logging

spark = SparkSession.builder.getOrCreate()
logger = logging.getLogger(__name__)

def run_monitor():
 """Execute monitoring logic"""
 try:
 # Your monitoring logic here
 df = spark.sql(f"""
 SELECT * FROM {config.get_table_path('your_table')}
 WHERE your_conditions
 """)
 
 results = df.collect()
 logger.info(f"Monitor completed: {len(results)} rows")
 
 return True, results
 except Exception as e:
 logger.error(f"Monitor failed: {str(e)}")
 return False, None

if __name__ == "__main__":
 run_monitor()
```

### Step 2: Update Orchestrator

Edit `orchestrator.py` and add to `monitoring_categories`:

```python
'custom_metrics': {
 'parallel': True, # or False if sequential
 'scripts': [
 'custom_metrics/new_monitor.sql'
 ],
 'priority': 1
}
```

### Step 3: Test

```bash
# Test script directly
dbx execute custom_metrics/new_monitor.sql

# Test via orchestrator
python orchestrator.py
```

### Step 4: Deploy

1. Commit script to Git
2. Update job definitions if needed
3. Monitor first production run
4. Add to dashboard if relevant

---

## Escalation Procedures

### Level 1: Self-Service (0-2 hours)

**Team Member Actions**:
* Check dashboard
* Review error logs
* Run on-demand health check
* Document findings

**Resolution**: 80% of issues

### Level 2: Platform Team (2-8 hours)

**Escalate If**:
* Multiple critical failures
* Data quality score < 60%
* Unable to resolve within 2 hours

**Contact**: 
* Slack: #sap-platform
* Email: platform-team@company.com

**Resolution**: 95% of issues

### Level 3: Senior Engineering (8-24 hours)

**Escalate If**:
* System-wide monitoring failure
* Production data corruption risk
* Compliance or audit concerns

**Contact**:
* On-call: PagerDuty rotation
* Escalation email: engineering-leads@company.com

**Resolution**: 99.9% of issues

### Level 4: Executive (24+ hours)

**Escalate If**:
* Business-critical system down
* Data breach or security incident
* Regulatory reporting at risk

**Contact**:
* CTO / VP Engineering
* Platform Director

---

## Change Management

### Adding/Modifying Monitors

1. **Development**
 * Create/update scripts in dev environment
 * Test locally with sample data
 * Update config.py if needed

2. **Testing**
 * Run full orchestration in dev
 * Validate results in monitoring tables
 * Check dashboard updates

3. **Review**
 * Code review by peer
 * Platform team approval
 * Document changes

4. **Deployment**
 * Merge to main branch
 * Deploy to production
 * Monitor first production run
 * Update runbooks if needed

### Configuration Changes

All configuration should go through `config.py`:
* Never hardcode table names in scripts
* Use environment variables for secrets
* Validate configuration on startup

---

## Additional Resources

* **Dashboard**: [SkillAIPath Monitoring Dashboard](#)
* **Jobs UI**: [Databricks Workflows](#)
* **Unity Catalog**: `sap_dev.monitoring`
* **Git Repo**: `/Shared/dev/SkillAIPath/4_Business_Intelligence/1_Monitoring_Observability`
* **Slack Channel**: #sap-monitoring

---

**Document Owner**: SkillAIPath Platform Team 
**Last Review**: 2026-07-11 
**Next Review**: 2026-08-11
