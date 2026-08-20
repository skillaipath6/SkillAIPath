# Quick Start Guide - SkillAIPath Monitoring

**Time to Read**: 5 minutes 
**For**: New team members, operators, support staff

---

## What You Need to Know

The SkillAIPath monitoring system runs automatically every day at 6 AM UTC and checks: **Data Quality** - Are our tables healthy? **Performance** - Are queries running efficiently? **Costs** - Are we spending wisely?

---

## Check System Health (2 minutes)

### Option 1: Dashboard (Recommended)
1. Open [SkillAIPath Monitoring Dashboard](#)
2. Look at the top 4 numbers:
 * **Last Run Status**: Should be GREEN * **Success Rate**: Should be >95%
 * **Recent Failures**: Should be 0 or 1-2 max
3. Done! If all green, system is healthy.

### Option 2: SQL Query
```sql
SELECT 
 status,
 scripts_success,
 scripts_failed,
 duration_seconds,
 run_timestamp
FROM sap_dev.monitoring.orchestration_runs
ORDER BY run_timestamp DESC
LIMIT 1;
```

**What to look for**:
* `status` = 'success' → All good
* `status` = 'partial_failure' → Some issues, check failures
* `status` = 'failed' → Multiple problems, escalate

---

## Something Failed - What Now?

### Step 1: Don't Panic
* Monitoring failures are usually transient (temporary)
* System has automatic retries built in
* Most issues resolve themselves

### Step 2: Check What Failed
```sql
SELECT 
 run_timestamp,
 scripts_failed,
 error_message
FROM sap_dev.monitoring.orchestration_runs
WHERE status != 'success'
 AND run_date >= CURRENT_DATE() - 7
ORDER BY run_timestamp DESC;
```

### Step 3: Take Action Based on Severity

**1-2 scripts failed**: 
* ⏰ Check again in 1 hour
* Likely fixed by next automatic run

**3+ scripts failed**:
* Investigate within 2 hours
* Check error_message for clues
* Run manual health check

**Critical data quality checks failed**:
* **IMMEDIATE ACTION**
* Check source data pipelines
* Notify platform team on Slack: #sap-platform

---

## Run Manual Health Check

Sometimes you want to run monitoring right now instead of waiting for scheduled run.

### Via UI:
1. Go to Databricks Workflows
2. Find "SkillAIPath_OnDemand_HealthCheck"
3. Click "Run Now"
4. Wait 10-15 minutes
5. Check results on dashboard

### Via Command Line:
```bash
databricks jobs run-now --job-name SkillAIPath_OnDemand_HealthCheck
```

---

## Understanding the Dashboard

### Top Row - KPIs
* **Last Run Status**: Latest monitoring execution result
* **Total Scripts**: How many checks are monitored
* **Success Rate**: Percentage of successful checks
* **Duration**: How long monitoring took

### Middle Rows - Trends
* **Daily Execution Trend**: Are we consistently successful?
* **Quality Score Trends**: Is data quality improving or degrading?
* **Cost Tracking**: Are costs within budget?

### Bottom Row - Action Items
* **Recent Failures**: What needs attention right now?
* **Optimization Needs**: Which tables need OPTIMIZE?
* **Top Issues**: Where should we focus improvement efforts?

---

## 🆘 Who to Contact

### Questions about monitoring:
* Slack: #sap-platform
* Email: platform-team@company.com

### Urgent issues (production down):
* PagerDuty: On-call rotation
* Slack: @platform-team (use @ to alert everyone)

### Documentation unclear:
* Slack: #sap-docs
* Submit PR to improve this guide!

---

## Pro Tips

1. **Check dashboard first thing every morning** (takes 30 seconds)
2. **Bookmark the dashboard** for quick access
3. **Subscribe to alerts** so you're notified automatically
4. **If something looks weird**, run on-demand health check to verify
5. **Document any workarounds** you discover (update this guide!)

---

## Learn More

* [Full Operations Guide](./operations_guide.md) - Complete detailed documentation
* [Troubleshooting Guide](./troubleshooting_guide.md) - Common issues and fixes
* [Architecture Overview](./architecture.md) - How everything works

---

**Remember**: This system is designed to be self-healing. Most issues resolve automatically. Your job is to watch for patterns and escalate only when needed.

**Questions?** Ask in #sap-platform - we're here to help! 