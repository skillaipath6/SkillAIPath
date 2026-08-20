# Troubleshooting Guide - SkillAIPath Monitoring

**Quick Reference for Common Issues**

---

## Diagnosis Decision Tree

```
Is monitoring running at all?
├─ NO → Check #1: Job Scheduling
└─ YES
 │
 Are results appearing in tables?
 ├─ NO → Check #2: Permissions
 └─ YES
 │
 Are specific scripts failing?
 ├─ YES → Check #3: Script-Specific Issues
 └─ NO
 │
 Are results unexpected/wrong?
 └─ YES → Check #4: Data Quality Issues
```

---

## ❌ Issue #1: Monitoring Job Not Running

### Symptoms
* No new runs in orchestration_runs table
* Dashboard shows stale data (>24 hours old)
* No email notifications received

### Diagnosis
```sql
-- Check last run time
SELECT MAX(run_timestamp) as last_run
FROM sap_dev.monitoring.orchestration_runs;

-- If last_run > 24 hours ago, job is not running
```

### Resolution Steps

**Step 1**: Check job schedule
```bash
databricks jobs list --output JSON | grep "SkillAIPath"
```

**Step 2**: Check if job is paused
* Go to Workflows UI
* Find "SkillAIPath_Daily_Monitoring"
* Check "Schedule" status
* If PAUSED, click "Resume"

**Step 3**: Check for job failures
```bash
databricks jobs list-runs --job-name SkillAIPath_Daily_Monitoring --limit 10
```

**Step 4**: Manual trigger to test
```bash
databricks jobs run-now --job-name SkillAIPath_Daily_Monitoring
```

### Prevention
* Set up monitoring for the monitoring (meta-monitoring)
* Add phase-based review of job history
* Enable email notifications for missed runs

---

## ❌ Issue #2: Permission Denied Errors

### Symptoms
* Scripts fail with "Permission denied" or "Access denied"
* Error mentions Unity Catalog or table names
* Some scripts succeed, others fail

### Common Permission Errors

#### Error: "Permission denied on schema sap_dev.monitoring"

**Cause**: User/service account lacks permissions on monitoring schema

**Fix**:
```sql
-- Grant necessary permissions
GRANT SELECT, MODIFY, CREATE ON SCHEMA sap_dev.monitoring TO `user@company.com`;

-- Or for service principal
GRANT SELECT, MODIFY, CREATE ON SCHEMA sap_dev.monitoring TO `service-sap-monitoring`;
```

#### Error: "Table or view not found: sap_dev.silver.fact_sales"

**Cause**: Table doesn't exist OR user lacks SELECT permission

**Diagnosis**:
```sql
-- Check if table exists
SHOW TABLES IN sap_dev.silver LIKE 'fact_sales';

-- Check your permissions
SHOW GRANTS ON TABLE sap_dev.silver.fact_sales;
```

**Fix**:
```sql
-- Grant SELECT if table exists
GRANT SELECT ON TABLE sap_dev.silver.fact_sales TO `user@company.com`;

-- Grant usage on catalog/schema
GRANT USAGE ON CATALOG sap_dev TO `user@company.com`;
GRANT USAGE ON SCHEMA sap_dev.silver TO `user@company.com`;
```

### Permission Checklist

Monitoring needs these permissions:

* `USAGE` on catalog `sap_dev`
* `USAGE` on schemas: `bronze`, `silver`, `gold`, `monitoring`
* `SELECT` on all source tables
* `SELECT, MODIFY, CREATE` on schema `sap_dev.monitoring`
* `SELECT, MODIFY` on monitoring result tables
* Access to `system.access.audit` (for cost tracking)
* Access to `system.query.history` (for performance monitoring)

---

## ❌ Issue #3: Specific Scripts Failing

### Script: data_quality_checks.sql

**Common Error**: "Column 'total_amount' not found"

**Cause**: Schema mismatch between script and actual table

**Fix**:
```sql
-- Check actual schema
DESCRIBE TABLE sap_dev.silver.fact_sales;

-- Update script to use correct column names
-- Edit: data_quality/data_quality_checks.sql
```

---

### Script: delta_optimization_metrics.sql

**Common Error**: "DESCRIBE DETAIL requires SELECT permission"

**Cause**: Missing SELECT permission on table

**Fix**:
```sql
-- Grant SELECT on all tables in layer
GRANT SELECT ON SCHEMA sap_dev.bronze TO monitoring_user;
GRANT SELECT ON SCHEMA sap_dev.silver TO monitoring_user;
GRANT SELECT ON SCHEMA sap_dev.gold TO monitoring_user;
```

---

### Script: cost_attribution.sql

**Common Error**: "system.access.audit not accessible"

**Cause**: Missing system table permissions (requires workspace admin or specific grant)

**Workaround**:
* Option 1: Request workspace admin to grant access
* Option 2: Use alternative cost tracking via cluster metrics
* Option 3: Disable cost_attribution script (comment out in orchestrator)

---

## ❌ Issue #4: Results Look Wrong

### Problem: Quality scores always 100%

**Cause**: Queries not finding actual data issues

**Diagnosis**:
```sql
-- Check if checks are actually running
SELECT 
 table_name,
 total_rows,
 null_count,
 duplicate_count
FROM sap_dev.monitoring.data_quality_results
WHERE check_date = CURRENT_DATE()
ORDER BY table_name;
```

**What to look for**:
* `total_rows = 0` → Query not finding data
* `null_count = 0` AND `duplicate_count = 0` → Checks too lenient
* `quality_score_pct = 100` for all tables → Logic issue

**Fix**:
* Review data_quality_checks.sql logic
* Add more strict validation rules
* Test queries manually on sample tables

### Problem: No data in monitoring tables

**Cause**: Results not being written

**Diagnosis**:
```sql
-- Check if any data exists
SELECT COUNT(*) FROM sap_dev.monitoring.orchestration_runs;

-- Check latest partition
SELECT MAX(run_date) FROM sap_dev.monitoring.orchestration_runs;
```

**Fix**:
* Check orchestrator.py persist_results() method
* Verify MODIFY permission on monitoring tables
* Check for transaction rollbacks in logs

---

## ❌ Issue #5: Performance - Scripts Running Slow

### Symptoms
* Orchestration takes >1 hour (normal is 15-20 min)
* Timeout errors
* High DBU costs

### Common Causes & Fixes

#### Cause 1: Large table scans

**Fix**: Add date filters to queries
```sql
-- Before (slow)
SELECT * FROM sap_dev.silver.fact_sales;

-- After (fast)
SELECT * FROM sap_dev.silver.fact_sales
WHERE sales_date >= CURRENT_DATE() - 30;
```

#### Cause 2: Too many small files

**Fix**: Run OPTIMIZE on source tables
```sql
OPTIMIZE sap_dev.silver.fact_sales;
OPTIMIZE sap_dev.silver.fact_purchase;
```

#### Cause 3: Inefficient joins

**Fix**: Use broadcast joins for small dimensions
```sql
SELECT /*+ BROADCAST(dim_product) */
 f.*, d.product_name
FROM fact_sales f
JOIN dim_product d ON f.product_id = d.product_id;
```

---

## Debugging Tools

### 1. Check Orchestrator Logs
```sql
-- View detailed execution log
SELECT * FROM sap_dev.monitoring.orchestration_runs
WHERE run_id = 'your-run-id'
ORDER BY run_timestamp DESC;
```

### 2. Test Individual Scripts
```bash
# Test SQL script directly
databricks workspace export /path/to/script.sql --format SOURCE | spark-sql

# Test Python script
python /Workspace/Shared/dev/SkillAIPath/.../script.py
```

### 3. Enable Debug Logging
Edit `orchestrator.py`:
```python
# Change from INFO to DEBUG
logging.basicConfig(level=logging.DEBUG)
```

### 4. Profile Query Performance
```sql
-- Enable query profiling
SET spark.sql.adaptive.enabled = true;
SET spark.sql.adaptive.coalescePartitions.enabled = true;

-- Run your query
EXPLAIN COST SELECT * FROM your_query;
```

---

## Still Stuck?

### Before Escalating, Gather:

1. **Error message** (full text)
2. **Run ID** from orchestration_runs table
3. **Timestamp** when issue occurred
4. **What you've tried** already

### Contact:

* **Slack**: #sap-platform (fastest response)
* **Email**: platform-team@company.com
* **Urgent**: PagerDuty on-call rotation

---

## Related Documentation

* [Operations Guide](./operations_guide.md) - Full operational procedures
* [Quick Start Guide](./quickstart_guide.md) - Basic operations
* [Architecture](./architecture.md) - System design and flow

---

**Last Updated**: 2026-07-11 
**Maintained By**: SkillAIPath Platform Team
