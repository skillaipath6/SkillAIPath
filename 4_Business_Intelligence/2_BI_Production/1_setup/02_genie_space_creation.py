# Databricks notebook source
# DBTITLE 1,Genie Spaces - Conversational Analytics
# MAGIC %md
# MAGIC # Genie Spaces - Conversational Analytics
# MAGIC **SkillAIPath Module 23 - Lakeview & Genie**
# MAGIC
# MAGIC ## What is Genie?
# MAGIC
# MAGIC **Genie** = ChatGPT for your data. Ask questions in natural language, get SQL results + visualizations.
# MAGIC
# MAGIC **Key Features:**
# MAGIC - Natural language queries ("Show me top 10 products by revenue")
# MAGIC - Auto-generates SQL from your Unity Catalog tables
# MAGIC - Understands business context (you teach it your metrics)
# MAGIC - Visualizations generated automatically
# MAGIC - FREE Edition Compatible (requires serverless SQL warehouse)
# MAGIC
# MAGIC **Launched:** 2024 (GA)
# MAGIC
# MAGIC **Use Case:** Enable non-technical users to explore data without writing SQL.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Why Genie for Interviews?
# MAGIC
# MAGIC **Common Interview Question:**
# MAGIC "How do you democratize data access for non-technical business stakeholders?"
# MAGIC
# MAGIC **Answer:**
# MAGIC 1. **Traditional:** Train everyone on SQL (expensive, slow)
# MAGIC 2. **Power BI:** Build fixed dashboards (not exploratory)
# MAGIC 3. **Genie Spaces:** Natural language queries on Unity Catalog (self-service analytics)
# MAGIC
# MAGIC **Portfolio Value:**
# MAGIC "Built conversational analytics with Genie Spaces, enabling 50+ business users to query 10TB data warehouse without SQL knowledge"
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## This Notebook
# MAGIC
# MAGIC **Goal:** Create a Genie Space for SkillAIPath data
# MAGIC
# MAGIC **Data Source:** All gold marts (customer_360, rfm_analysis, product_performance, revenue_dashboard)
# MAGIC
# MAGIC **Deliverable:** Genie Space where SkillAIPath Developers can ask:
# MAGIC - "What are our top 5 products this month?"
# MAGIC - "Show me customer churn rate by region"
# MAGIC - "Which stores have declining sales?"
# MAGIC
# MAGIC **Time:** 10 minutes (UI walkthrough)

# COMMAND ----------

# DBTITLE 1,Config & Prerequisites
# MAGIC %run /Workspace/Shared/dev/SkillAIPath/00_UTILS/01_config
# MAGIC
# MAGIC print("="*70)
# MAGIC print("GENIE SPACE CREATION")
# MAGIC print("="*70)
# MAGIC print(f"Environment: {Config.ENVIRONMENT}")
# MAGIC print(f"Gold Schema: {Config.SCHEMA_GOLD}")
# MAGIC print("="*70)
# MAGIC print()
# MAGIC print("PREREQUISITES:")
# MAGIC print("- Databricks FREE Edition with serverless warehouse (included)")
# MAGIC print("- Module 05_GOLD completed (all gold marts exist)")
# MAGIC print("- Unity Catalog enabled")
# MAGIC print("="*70)

# COMMAND ----------

# DBTITLE 1,List Available Gold Marts
# Show all gold marts available for Genie
tables_in_gold = spark.sql(f"SHOW TABLES IN {Config.CATALOG}.{Config.SCHEMA_GOLD}").collect()

print(f"Gold marts available for Genie Space ({len(tables_in_gold)} tables):")
print("="*70)

for table in tables_in_gold:
    table_name = table.tableName
    row_count = spark.read.table(f"{Config.CATALOG}.{Config.SCHEMA_GOLD}.{table_name}").count()
    print(f"- {table_name}: {row_count:,} rows")

print("="*70)
print()
print("These tables will be available for natural language queries in Genie.")

# COMMAND ----------

# DBTITLE 1,Step 1: Navigate to Genie
# MAGIC %md
# MAGIC ## Step 1: Navigate to Genie
# MAGIC
# MAGIC **UI Path:**
# MAGIC 1. Click **SQL** in left sidebar
# MAGIC 2. Click **Genie Spaces** (under SQL section)
# MAGIC 3. Click **Create Genie Space** button
# MAGIC
# MAGIC **Alternative:**
# MAGIC - Go directly to: `https://<your-workspace>.cloud.databricks.com/genie`
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **What You'll See:**
# MAGIC - Space name input
# MAGIC - Table selection dropdown
# MAGIC - Description field (optional)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **IMPORTANT:** Genie is UI-based - this notebook guides you through manual setup.

# COMMAND ----------

# DBTITLE 1,Step 2: Configure Genie Space
# MAGIC %md
# MAGIC ## Step 2: Configure Genie Space
# MAGIC
# MAGIC **In Genie UI:**
# MAGIC
# MAGIC 1. **Space Name:** "SkillAIPath Analytics"
# MAGIC
# MAGIC 2. **Description:**
# MAGIC    "Conversational analytics for SkillAIPath retail data. Ask questions about customers, products, sales, and inventory."
# MAGIC
# MAGIC 3. **Select Tables:** Choose ALL gold marts:
# MAGIC    - `sap_gold.mart_customer_360`
# MAGIC    - `sap_gold.mart_rfm_analysis`
# MAGIC    - `sap_gold.mart_product_performance`
# MAGIC    - `sap_gold.mart_revenue_dashboard`
# MAGIC    - `sap_gold.mart_inventory_health`
# MAGIC
# MAGIC 4. **Instructions for Genie (optional but recommended):**
# MAGIC
# MAGIC ```
# MAGIC Business Context:
# MAGIC - SkillAIPath is a retail chain with 20 stores across India
# MAGIC - We track customer purchases, inventory, and product performance
# MAGIC - Fiscal year runs Apr-Mar
# MAGIC
# MAGIC Key Metrics:
# MAGIC - RFM Score: Customer segmentation (1-5, higher is better)
# MAGIC - Churn: Customer inactive for 90+ days
# MAGIC - Stock Turnover: Inventory sold per month
# MAGIC
# MAGIC Common Questions:
# MAGIC - Top products, customers, stores by revenue
# MAGIC - Customer churn analysis by region
# MAGIC - Inventory health (overstock, understock)
# MAGIC ```
# MAGIC
# MAGIC 5. Click **Create Space**
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Result:** Genie Space ready for natural language queries

# COMMAND ----------

# DBTITLE 1,Step 3: Test with Sample Questions
# MAGIC %md
# MAGIC ## Step 3: Test with Sample Questions
# MAGIC
# MAGIC **Ask Genie (type in chat box):**
# MAGIC
# MAGIC ### Question 1: Revenue Analysis
# MAGIC **You:** "What are the top 10 products by revenue this year?"
# MAGIC
# MAGIC **Genie generates:**
# MAGIC ```sql
# MAGIC SELECT
# MAGIC     ProductName,
# MAGIC     SUM(TotalRevenue) AS Revenue
# MAGIC FROM sap_gold.mart_product_performance
# MAGIC WHERE Year = YEAR(CURRENT_DATE)
# MAGIC GROUP BY ProductName
# MAGIC ORDER BY Revenue DESC
# MAGIC LIMIT 10
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Question 2: Customer Segmentation
# MAGIC **You:** "Show me RFM distribution - how many customers in each segment?"
# MAGIC
# MAGIC **Genie generates:**
# MAGIC ```sql
# MAGIC SELECT
# MAGIC     RFMSegment,
# MAGIC     COUNT(*) AS CustomerCount
# MAGIC FROM sap_gold.mart_rfm_analysis
# MAGIC GROUP BY RFMSegment
# MAGIC ORDER BY CustomerCount DESC
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Question 3: Churn Analysis
# MAGIC **You:** "Which cities have the highest customer churn rate?"
# MAGIC
# MAGIC **Genie generates:**
# MAGIC ```sql
# MAGIC SELECT
# MAGIC     City,
# MAGIC     COUNT(CASE WHEN ChurnFlag = 1 THEN 1 END) * 100.0 / COUNT(*) AS ChurnRate
# MAGIC FROM sap_gold.mart_customer_360
# MAGIC GROUP BY City
# MAGIC ORDER BY ChurnRate DESC
# MAGIC LIMIT 10
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Pro Tip:** If Genie misunderstands, refine your question or add context to Space instructions.

# COMMAND ----------

# DBTITLE 1,Step 4: Teach Genie Business Terms
# MAGIC %md
# MAGIC ## Step 4: Teach Genie Business Terms
# MAGIC
# MAGIC **Add Custom Instructions** (improves accuracy):
# MAGIC
# MAGIC 1. Click **Settings** in Genie Space
# MAGIC 2. Add to **Instructions:**
# MAGIC
# MAGIC ```
# MAGIC Glossary:
# MAGIC - "High-value customers" = RFM Score >= 4
# MAGIC - "Churned customers" = ChurnFlag = 1
# MAGIC - "Overstocked" = StockLevel > 2x MonthlyDemand
# MAGIC - "Understocked" = StockLevel < 0.5x MonthlyDemand
# MAGIC - "Top performers" = Top 20% by Revenue
# MAGIC
# MAGIC Metric Definitions:
# MAGIC - CLV (Customer Lifetime Value) = TotalRevenue from customer
# MAGIC - NPS (Net Promoter Score) = Not tracked in this dataset
# MAGIC - Basket Size = Average items per transaction
# MAGIC
# MAGIC Date Filters:
# MAGIC - "This month" = current calendar month
# MAGIC - "Last quarter" = previous 3 months
# MAGIC - "YTD" = Year to date (Jan 1 to today)
# MAGIC ```
# MAGIC
# MAGIC 3. Click **Save**
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Result:** Genie now understands your business terminology

# COMMAND ----------

# DBTITLE 1,Step 5: Share with Team
# MAGIC %md
# MAGIC ## Step 5: Share with Team
# MAGIC
# MAGIC **Make Genie Space Available:**
# MAGIC
# MAGIC 1. Click **Share** button (top right)
# MAGIC 2. Add users or groups:
# MAGIC    - **Viewers:** Can ask questions, see results
# MAGIC    - **Editors:** Can modify Space instructions
# MAGIC    - **Admins:** Full control
# MAGIC
# MAGIC 3. Copy Genie Space URL
# MAGIC 4. Share with business stakeholders
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Access Control:**
# MAGIC - Genie respects Unity Catalog permissions
# MAGIC - SkillAIPath Developers can only query tables they have SELECT on
# MAGIC - Row-level security (ABAC policies) automatically applied
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Usage Tracking:**
# MAGIC - Genie logs all queries in system tables
# MAGIC - Track which questions users ask most
# MAGIC - Refine Space instructions based on patterns
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Result:** Self-service analytics for entire organization

# COMMAND ----------

# DBTITLE 1,Portfolio Tips
# MAGIC %md
# MAGIC ## Portfolio Tips - Genie Spaces
# MAGIC
# MAGIC **Resume Bullet:**
# MAGIC "Deployed conversational analytics with Genie Spaces, enabling 50+ non-technical users to query 10TB data warehouse using natural language (95% query accuracy, zero SQL training required)"
# MAGIC
# MAGIC **Interview Talking Points:**
# MAGIC
# MAGIC 1. **ROI Calculation:**
# MAGIC    - Traditional: 40 hours SQL training per user = 2,000 hours for 50 users
# MAGIC    - Genie: 1 hour onboarding per user = 50 hours
# MAGIC    - **Savings:** 1,950 hours = $97,500 (at $50/hour)
# MAGIC
# MAGIC 2. **Adoption Metrics:**
# MAGIC    - Track queries per user per week
# MAGIC    - Measure question accuracy (% requiring refinement)
# MAGIC    - Monitor most-asked questions (improve Space instructions)
# MAGIC
# MAGIC 3. **Security:**
# MAGIC    - Unity Catalog permissions inherited
# MAGIC    - ABAC policies for row-level security
# MAGIC    - Audit trail for all queries
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Common Mistake:**
# MAGIC Don't expose bronze/silver tables to Genie - only curated gold marts with clean column names and descriptions.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - Module 23 Notebook 03: Self-service Excel to Genie automation
# MAGIC - Module 23 Notebook 04: SQL alerts for data quality

# COMMAND ----------

