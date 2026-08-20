
# Unity Catalog PII Masking & Row Filters - Complete Setup Guide

## **PURPOSE**
Enable Unity Catalog governance features (column masking, row filters, ABAC) for production-ready data security.

---

## **PREREQUISITES**

### Required Permissions:
You need ONE of these permission levels:

1. **Metastore Admin** (recommended for enterprise setup)
2. **Table Owner** (can set policies on owned tables only)
3. **Catalog Owner** (can delegate permissions)

### Check Your Permissions:

```sql
-- Check if you're metastore admin
SHOW GRANTS ON METASTORE;

-- Check table ownership
DESCRIBE TABLE EXTENDED sap_dev.gold.mart_customer_360;
-- Look for "Owner" field

-- Check catalog permissions
SHOW GRANTS ON CATALOG sap_dev;
```

---

## **STEP 1: Request Required Permissions** (If Needed)

### Option A: Ask Your Workspace Admin

**Email Template:**
```
Subject: Request: Unity Catalog Governance Permissions for SkillAIPath Project

Hi [Admin Name],

I'm working on the SkillAIPath data governance project and need permissions to implement 
PII masking and row-level security on the following tables:

Tables:
- sap_dev.gold.mart_customer_360 (customer PII)
- sap_dev.gold.mart_rfm_analysis (revenue data)

I need ONE of:
1. Metastore Admin role (preferred for full governance setup)
2. Table Owner permissions on above tables
3. GRANT CREATE FUNCTION ON CATALOG sap_dev

Use Case: Implementing column masking for PII fields (phone, email) and row filters 
for regional data access control.

Expected Timeline: Testing this week, production deployment next week.

Thanks,
[Your Name]
```

### Option B: Work on Tables You Own

If you created the tables (e.g., via your own notebooks), you already have Owner permissions!

```sql
-- Verify you own the table
DESCRIBE TABLE EXTENDED sap_dev.gold.mart_customer_360;
-- If "Owner: your_email@company.com" appears, you're ready to go!
```

---

## **STEP 2: Create User Groups** (One-Time Setup)

### Why Groups?
Column masks and row filters use `is_member('group_name')` checks. Define groups once, manage users centrally.

### Setup (Requires Workspace Admin):

```sql
-- Create groups for different access levels
CREATE GROUP compliance_team;
CREATE GROUP data_analysts;
CREATE GROUP north_finance;
CREATE GROUP south_finance;
CREATE GROUP executives;

-- Add users to groups
ALTER GROUP compliance_team ADD USER alice@company.com;
ALTER GROUP compliance_team ADD USER bob@company.com;

ALTER GROUP data_analysts ADD USER charlie@company.com;
ALTER GROUP data_analysts ADD USER dana@company.com;

ALTER GROUP executives ADD USER ceo@company.com;
```

### Alternative: Use Existing Groups

Check existing groups in your workspace:
```sql
SHOW GROUPS;
```

Common groups you can reuse:
- `admins`
- `users`
- Department-based groups (finance, marketing, engineering)

---

## **STEP 3: Implement Column Masking for PII** (10 minutes)

### Example: Mask Customer Phone Numbers

```sql
-- Create masking function
CREATE OR REPLACE FUNCTION sap_dev.gold.mask_phone(phone_number STRING)
RETURN CASE
 WHEN is_member('compliance_team') THEN phone_number
 WHEN is_member('executives') THEN phone_number
 ELSE CONCAT('XXX-XXX-', SUBSTRING(phone_number, -4, 4))
END;

-- Apply mask to column
ALTER TABLE sap_dev.gold.mart_customer_360
ALTER COLUMN PhoneNumber SET MASK sap_dev.gold.mask_phone;
```

### Example: Mask Customer Email

```sql
-- Create email masking function
CREATE OR REPLACE FUNCTION sap_dev.gold.mask_email(email STRING)
RETURN CASE
 WHEN is_member('compliance_team') THEN email
 WHEN is_member('executives') THEN email
 ELSE CONCAT(SUBSTRING(email, 1, 3), '***@', SPLIT(email, '@')[1])
END;

-- Apply mask to column
ALTER TABLE sap_dev.gold.mart_customer_360
ALTER COLUMN Email SET MASK sap_dev.gold.mask_email;
```

### Test Masking:

```sql
-- As compliance team member (sees real values):
SELECT PhoneNumber, Email FROM sap_dev.gold.mart_customer_360 LIMIT 5;
-- Result: +91-98765-43210, alice.smith@example.com

-- As data analyst (sees masked values):
SELECT PhoneNumber, Email FROM sap_dev.gold.mart_customer_360 LIMIT 5;
-- Result: XXX-XXX-3210, ali***@example.com
```

---

## **STEP 4: Implement Row-Level Security** (10 minutes)

### Example: Filter Customers by Region

```sql
-- Create row filter function
CREATE OR REPLACE FUNCTION sap_dev.gold.filter_by_region(customer_region STRING)
RETURN CASE
 WHEN is_member('executives') THEN TRUE
 WHEN is_member('compliance_team') THEN TRUE
 WHEN is_member('north_finance') AND customer_region = 'North' THEN TRUE
 WHEN is_member('south_finance') AND customer_region = 'South' THEN TRUE
 WHEN is_member('east_finance') AND customer_region = 'East' THEN TRUE
 WHEN is_member('west_finance') AND customer_region = 'West' THEN TRUE
 ELSE FALSE
END;

-- Apply row filter to table
ALTER TABLE sap_dev.gold.mart_customer_360
SET ROW FILTER sap_dev.gold.filter_by_region ON (Region);
```

### Test Row Filtering:

```sql
-- As executive (sees all regions):
SELECT Region, COUNT(*) FROM sap_dev.gold.mart_customer_360 GROUP BY Region;
-- Result: North: 5000, South: 4500, East: 5200, West: 4637

-- As north_finance member (sees only North):
SELECT Region, COUNT(*) FROM sap_dev.gold.mart_customer_360 GROUP BY Region;
-- Result: North: 5000

-- Attempts to query other regions return 0 rows automatically
```

---

## **STEP 5: Remove Policies (If Needed)**

### Remove Column Masking:

```sql
-- Remove mask from phone number
ALTER TABLE sap_dev.gold.mart_customer_360
ALTER COLUMN PhoneNumber DROP MASK;

-- Remove mask from email
ALTER TABLE sap_dev.gold.mart_customer_360
ALTER COLUMN Email DROP MASK;
```

### Remove Row Filter:

```sql
-- Remove row filter
ALTER TABLE sap_dev.gold.mart_customer_360
DROP ROW FILTER;
```

---

## **COMPLETE GOVERNANCE EXAMPLE**

### Full Implementation for mart_customer_360:

```sql
-- 1. Create all masking functions
CREATE OR REPLACE FUNCTION sap_dev.gold.mask_phone(phone STRING)
RETURN CASE
 WHEN is_member('compliance_team') THEN phone
 ELSE CONCAT('XXX-XXX-', SUBSTRING(phone, -4, 4))
END;

CREATE OR REPLACE FUNCTION sap_dev.gold.mask_email(email STRING)
RETURN CASE
 WHEN is_member('compliance_team') THEN email
 ELSE CONCAT(SUBSTRING(email, 1, 3), '***@', SPLIT(email, '@')[1])
END;

CREATE OR REPLACE FUNCTION sap_dev.gold.mask_name(name STRING)
RETURN CASE
 WHEN is_member('compliance_team') THEN name
 ELSE CONCAT(SUBSTRING(name, 1, 1), '*** ', SPLIT(name, ' ')[SIZE(SPLIT(name, ' '))])
END;

-- 2. Create row filter function
CREATE OR REPLACE FUNCTION sap_dev.gold.filter_customer_access(region STRING, lifetime_value DECIMAL)
RETURN CASE
 WHEN is_member('executives') THEN TRUE
 WHEN is_member('compliance_team') THEN TRUE
 WHEN is_member('north_finance') AND region = 'North' THEN TRUE
 WHEN is_member('south_finance') AND region = 'South' THEN TRUE
 WHEN is_member('vip_analysts') AND lifetime_value > 50000 THEN TRUE
 ELSE FALSE
END;

-- 3. Apply all policies
ALTER TABLE sap_dev.gold.mart_customer_360
ALTER COLUMN PhoneNumber SET MASK sap_dev.gold.mask_phone;

ALTER TABLE sap_dev.gold.mart_customer_360
ALTER COLUMN Email SET MASK sap_dev.gold.mask_email;

ALTER TABLE sap_dev.gold.mart_customer_360
ALTER COLUMN CustomerName SET MASK sap_dev.gold.mask_name;

ALTER TABLE sap_dev.gold.mart_customer_360
SET ROW FILTER sap_dev.gold.filter_customer_access ON (Region, LifetimeValue);
```

---

## **VERIFICATION & TESTING**

### Test Different User Personas:

```python
# Test as different users (run in separate sessions)
test_users = {
 "compliance@company.com": "compliance_team", # Sees everything
 "analyst@company.com": "data_analysts", # Sees masked PII
 "north_mgr@company.com": "north_finance", # Sees only North region, masked PII
}

# Expected behavior:
# - compliance_team: Full access, no masking, all rows
# - data_analysts: All rows, masked PII
# - north_finance: Only North rows, masked PII
```

---

## **TROUBLESHOOTING**

### Issue: "User does not have CREATE FUNCTION permission"
**Solution:** Request `GRANT CREATE FUNCTION ON CATALOG sap_dev` from admin.

### Issue: "Cannot alter table: not an owner"
**Solution:** Request table ownership: `ALTER TABLE ... OWNER TO user@email.com`

### Issue: "Function not found"
**Solution:** Verify function exists: `SHOW FUNCTIONS IN sap_dev.gold LIKE 'mask*'`

### Issue: "Masking not working"
**Solution:** 
1. Check user groups: `SHOW GROUP MEMBERSHIPS FOR user@email.com`
2. Verify mask is applied: `DESCRIBE TABLE EXTENDED sap_dev.gold.mart_customer_360`

---

## **PRODUCTION DEPLOYMENT CHECKLIST**

- [ ] Permissions verified (metastore admin or table owner)
- [ ] User groups created and populated
- [ ] Masking functions tested with different user personas
- [ ] Row filters tested with regional access
- [ ] Documentation updated with governance policies
- [ ] Audit logging enabled (Unity Catalog tracks all access automatically)
- [ ] Business stakeholders approved policies
- [ ] Rollback plan defined (DROP MASK / DROP ROW FILTER commands ready)

---

## **SUPPORT & RESOURCES**

- **Unity Catalog Docs:** https://docs.databricks.com/data-governance/unity-catalog/index.html
- **Column Masking:** https://docs.databricks.com/security/privacy/column-masking.html
- **Row Filters:** https://docs.databricks.com/security/privacy/row-filters.html
- **ABAC Policies:** https://docs.databricks.com/security/privacy/attribute-based-access-control.html

---

## **BUSINESS VALUE**

**Before Unity Catalog Governance:**
- 12 separate views for different teams/regions
- Manual permission management
- PII exposure risk
- View sprawl and maintenance overhead

**After Unity Catalog Governance:**
- 1 table with centralized policies
- Automatic enforcement across all query tools
- Zero PII exposure to unauthorized users
- Policies defined in SQL, version-controlled in Git

**ROI:** 80% reduction in view maintenance time, 100% PII compliance

