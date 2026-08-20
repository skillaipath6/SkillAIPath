# Standard Operating Procedures (SOPs) for Domain Templates V2

**Decision Trees, Guidelines, and Best Practices**

---

## SOP 1: Determining What Can Be Automated

### Decision Tree

```
START: User provides data/requirements
 ↓
├─ Is there structured data (CSV/XLSX)?
│ ├─ YES → AUTO: Schema extraction, Bronze setup
│ └─ NO → MANUAL: Define schema manually
│
├─ Are relationships obvious from column names? (e.g., participant_id, project_id)
│ ├─ YES → AUTO: Detect joins, create Silver models
│ └─ NO → SEMI-AUTO: Suggest, human confirms
│
├─ Are metrics standard aggregations? (COUNT, SUM, AVG)
│ ├─ YES → AUTO: Generate Gold metrics
│ └─ NO → MANUAL: Define custom KPI logic
│
├─ Is business context documented? (PDF requirements)
│ ├─ YES → SEMI-AUTO: Parse, human validates
│ └─ NO → MANUAL: Interview stakeholders
│
└─ Is there existing dashboard? (PBIX, Tableau)
 ├─ YES → SEMI-AUTO: Extract layout, rebuild
 └─ NO → SEMI-AUTO: Template + human customizes
```

### Guidelines

| Scenario | Automation | Action |
|----------|-----------|--------|
| Column names follow conventions (`_id`, `_date`, `_amount`) | 90% | Auto-generate, quick review |
| Custom business rules ("active = last order < 90 days") | 20% | Generate template, human adds logic |
| Data quality rules ("revenue > 0 except refunds") | 10% | Human defines, system enforces |
| Dashboard aesthetics (colors, fonts, layout) | 30% | Template + human customizes |

---

## SOP 2: When to Use Dev vs UAT vs Production

### Decision Matrix

| Activity | Environment | Rationale |
|----------|------------|-----------|
| **Initial generation from files** | Dev | Expect issues, need fast iteration |
| **Adding new metrics/columns** | Dev | Test first, may need multiple attempts |
| **Fixing data quality issues** | Dev | Source data problems need investigation |
| **UI/UX tweaks** | Dev | Subjective, needs user feedback |
| **Stakeholder review** | UAT | Clean environment for sign-off |
| **Performance testing** | UAT | Production-like data volumes |
| **Final approval** | UAT | Last checkpoint before go-live |
| **Live reporting** | Production | Scheduled, monitored, stable |

### Promotion Criteria

**Dev → UAT:**
- [ ] All technical errors resolved
- [ ] User testing complete (2+ users)
- [ ] Data quality checks pass
- [ ] Documentation updated
- [ ] Dev team sign-off

**UAT → Production:**
- [ ] Business stakeholder approval
- [ ] Performance benchmarks met (<5s queries)
- [ ] Security review complete
- [ ] Monitoring/alerting configured
- [ ] Rollback plan documented

---

## SOP 3: Handling Complex Business Logic

### Decision Tree

```
START: Business requirement stated
 ↓
├─ Can it be expressed in SQL WHERE/HAVING?
│ ├─ YES → Add to YAML filters
│ └─ NO → Continue
│
├─ Does it involve multiple steps?
│ ├─ YES → Create intermediate Silver model
│ └─ NO → Continue
│
├─ Does it need window functions (LAG, LEAD, ROW_NUMBER)?
│ ├─ YES → Add to Silver transformation
│ └─ NO → Continue
│
└─ Is it procedural logic (if/then/case statements)?
 ├─ YES → Implement in Python notebook
 └─ NO → Escalate to architect
```

### Examples

**EXAMPLE 1: Engineer Attendance Status**

**Requirement:** "Engineer is 'at-risk' if attendance < 70% and GPA < 2.5"

**Decision:** Simple SQL logic
**Action:**
```yaml
silver:
 models:
 - name: participant_status
 source: bronze.fact_attendance
 transformations:
 - add_column:
 name: risk_status
 expression: |
 CASE 
 WHEN attendance_rate < 0.70 AND gpa < 2.5 THEN 'at-risk'
 WHEN attendance_rate < 0.85 THEN 'watch-list'
 ELSE 'good-standing'
 END
```

**EXAMPLE 2: Session Streak Calculation**

**Requirement:** "Count consecutive days a engineer attended"

**Decision:** Requires window functions
**Action:**
```yaml
silver:
 models:
 - name: session_streaks
 source: bronze.fact_session
 transformations:
 - window_function:
 name: days_since_last
 expression: |
 DATEDIFF(
 session_date,
 LAG(session_date) OVER (PARTITION BY participant_id ORDER BY session_date)
 )
 - add_column:
 name: streak_group
 expression: |
 SUM(CASE WHEN days_since_last > 1 THEN 1 ELSE 0 END)
 OVER (PARTITION BY participant_id ORDER BY session_date)
```

**EXAMPLE 3: Dynamic Cohort Analysis**

**Requirement:** "Group engineers by enrollment month, track retention over time"

**Decision:** Multi-step transformation
**Action:**
```yaml
silver:
 models:
 - name: participant_cohorts
 source: bronze.dim_participant
 transformations:
 - add_column:
 name: cohort_month
 expression: DATE_TRUNC('month', enrollment_date)
 
 - name: cohort_retention
 source: silver.participant_cohorts
 joins:
 - table: bronze.fact_session
 type: left
 on: participant_id
 transformations:
 - aggregate:
 group_by: [cohort_month, session_month]
 measures:
 active_participants: COUNT(DISTINCT participant_id)
 retention_rate: active_participants / first_value(active_participants)
```

---

## SOP 4: Adding Technical Development Instructions to YAML

### Template for Adding Dev Instructions

```yaml
# At top of YAML config
metadata:
 domain: learning_platform
 version: "1.0"
 last_updated: "2025-01-24"
 
 # TECHNICAL DEVELOPMENT INSTRUCTIONS
 dev_instructions:
 # Data modeling decisions
 modeling:
 - decision: "Use SCD Type 2 for dim_participant"
 rationale: "Need to track changes in engineer status over time"
 implemented_by: "auto_generator"
 
 - decision: "Incremental load for fact_session"
 rationale: "Large table, only new sessions added daily"
 implemented_by: "bronze_generator"
 
 - decision: "Pre-aggregate to daily level in Gold"
 rationale: "Dashboard only shows daily trends, saves compute"
 implemented_by: "gold_generator"
 
 # Business rule mappings
 business_rules:
 - rule: "Active engineer = attended in last 30 days"
 location: "silver.participant_status.is_active"
 reference: "Learning Platform T.pdf, Page 5"
 
 - rule: "Completion rate = completed_tasks / total_tasks"
 location: "gold.metrics.avg_completion_rate"
 reference: "Stakeholder email 2025-01-15"
 
 # Edge cases and exceptions
 edge_cases:
 - scenario: "Engineer with no sessions"
 handling: "Include in dim but exclude from metrics"
 location: "gold.metrics (WHERE clause)"
 
 - scenario: "Task marked complete after project end"
 handling: "Count as complete, flag for review"
 location: "silver.fact_task.late_completion_flag"
 
 # Performance optimizations
 performance:
 - optimization: "Partition fact_session by month"
 impact: "Reduce query time from 45s to 3s"
 implemented: true
 
 - optimization: "Z-order by participant_id on large tables"
 impact: "Improve join performance 10x"
 implemented: false
 reason: "Waiting for data volume to justify"
 
 # Testing requirements
 testing:
 - test: "Total engineers matches source Excel"
 validation: "COUNT(DISTINCT participant_id) = 1,247"
 status: "passed"
 
 - test: "No future-dated sessions"
 validation: "MAX(session_date) <= CURRENT_DATE"
 status: "pending"
```

### How Generators Use Dev Instructions

**1. Bronze Generator:**
- Reads `dev_instructions.modeling`
- Applies incremental load patterns
- Sets up partitioning

**2. Silver Generator:**
- Reads `dev_instructions.business_rules`
- Implements transformations
- Adds edge case handling

**3. Gold Generator:**
- Reads `dev_instructions.performance`
- Applies optimizations
- Creates validated metrics

**4. All Generators:**
- Log decisions in output
- Generate documentation
- Create test cases

---

## SOP 5: Quality Gates and Checkpoints

### Pre-Deployment Checklist

#### Dev Environment
```
☐ Schema validation
 ├─ All columns have types defined
 ├─ Primary keys identified
 └─ Foreign keys validated

☐ Data quality checks
 ├─ No nulls in required fields
 ├─ Date ranges reasonable
 └─ Numeric values in expected ranges

☐ Code generation
 ├─ All notebooks run without errors
 ├─ SQL queries are valid
 └─ Joins produce expected row counts

☐ User testing
 ├─ At least 2 users tested
 ├─ All critical paths verified
 └─ Feedback documented
```

#### UAT Environment
```
☐ Business validation
 ├─ Metrics match definitions
 ├─ Dashboard layout approved
 └─ Report outputs correct

☐ Performance
 ├─ Queries complete < 5 seconds
 ├─ Dashboard loads < 3 seconds
 └─ Job completes within SLA

☐ Security & governance
 ├─ PII columns tagged
 ├─ Access controls set
 └─ Audit logging enabled

☐ Documentation
 ├─ User guide complete
 ├─ Metric definitions documented
 └─ Troubleshooting guide ready
```

#### Production
```
☐ Deployment validation
 ├─ All assets created successfully
 ├─ Scheduling configured
 └─ Monitoring active

☐ Post-deployment
 ├─ First 3 runs monitored
 ├─ Alerts functioning
 └─ Users notified

☐ Operational readiness
 ├─ Support team trained
 ├─ Incident procedures documented
 └─ Rollback tested
```

---

## SOP 6: Troubleshooting Decision Tree

```
START: Issue reported
 ↓
├─ Is it a data issue?
│ ├─ Wrong values → Check source data + transformations
│ ├─ Missing data → Check Bronze ingestion + scheduling
│ └─ Unexpected nulls → Check join conditions
│
├─ Is it a performance issue?
│ ├─ Slow query → Check indexes, partitioning
│ ├─ Job timeout → Break into smaller tasks
│ └─ Dashboard slow → Pre-aggregate in Gold
│
├─ Is it a logic issue?
│ ├─ Wrong metric → Review YAML definition
│ ├─ Incorrect join → Check FK relationships
│ └─ Missing rows → Check WHERE clauses
│
└─ Is it an access issue?
 ├─ Permission denied → Check Unity Catalog grants
 ├─ Table not found → Verify catalog/schema names
 └─ Dashboard not visible → Check sharing settings
```

---

## Quick Reference: When to Do What

| Task | Auto | Semi | Manual | Time |
|------|------|------|--------|------|
| **Parse CSV/XLSX** | ✓ | | | 2 min |
| **Detect data types** | ✓ | | | 1 min |
| **Identify PK/FK** | ✓ | | | 1 min |
| **Generate Bronze** | ✓ | | | 5 min |
| **Basic Silver joins** | ✓ | | | 5 min |
| **Complex transformations** | | ✓ | | 30 min |
| **Standard metrics** | ✓ | | | 2 min |
| **Custom KPIs** | | | ✓ | 20 min |
| **Dashboard layout** | ✓ | | | 5 min |
| **Dashboard styling** | | ✓ | | 15 min |
| **PII detection** | ✓ | | | 30 sec |
| **Security policies** | | | ✓ | 1 hour |
| **Job scheduling** | ✓ | | | 2 min |
| **Business sign-off** | | | ✓ | varies |

---

**KEY PRINCIPLE: Automate the boilerplate, human adds the intelligence!**
