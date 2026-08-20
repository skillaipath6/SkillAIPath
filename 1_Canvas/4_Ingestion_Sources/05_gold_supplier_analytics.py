# Databricks notebook source
# DBTITLE 1,Supplier Performance Analytics - Gold Layer
# MAGIC %md
# MAGIC # Supplier Performance & Cost Optimization - Gold Analytics
# MAGIC
# MAGIC **Business Value:** Executive-ready supplier intelligence and cost optimization recommendations
# MAGIC
# MAGIC **Analytics Objectives:**
# MAGIC - Identify overpriced suppliers and quantify savings opportunities
# MAGIC - Rank suppliers by cost competitiveness vs industry benchmarks
# MAGIC - Recommend supplier diversification to reduce concentration risk
# MAGIC - Generate actionable procurement insights for negotiations
# MAGIC
# MAGIC **Input Tables:**
# MAGIC - `sap_dev.silver.ext_supplier_cost_benchmark` - Cost comparison analysis
# MAGIC - `sap_dev.silver.ext_product_sourcing_alternatives` - Alternative supplier options
# MAGIC - `sap_dev.silver.fact_purchases` - Purchase history
# MAGIC
# MAGIC **Output Marts:**
# MAGIC - `sap_dev.gold.mart_supplier_performance` - Supplier scorecard with KPIs
# MAGIC - `sap_dev.gold.mart_cost_optimization_opportunities` - Top savings opportunities

# COMMAND ----------

# DBTITLE 1,Load Config
# MAGIC %run ../../1_Canvas/1_Setup/1_config

# COMMAND ----------

# DBTITLE 1,Create Supplier Performance Mart
# MAGIC %sql
# MAGIC -- Build comprehensive supplier performance scorecard
# MAGIC CREATE OR REPLACE TABLE {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_supplier_performance AS
# MAGIC WITH supplier_stats AS (
# MAGIC     SELECT 
# MAGIC         wholesalerkey as supplier_id,
# MAGIC         COUNT(DISTINCT productkey) as products_supplied,
# MAGIC         COUNT(*) as purchase_transactions,
# MAGIC         SUM(total_quantity_purchased) as total_units_purchased,
# MAGIC         AVG(avg_your_cost) as avg_cost_per_unit,
# MAGIC         SUM(avg_your_cost * total_quantity_purchased) as total_spend,
# MAGIC         AVG(cost_variance_pct) as avg_cost_variance_pct,
# MAGIC         SUM(potential_savings) as total_potential_savings,
# MAGIC         MAX(supplier_concentration_risk) as risk_level,
# MAGIC         AVG(alternative_suppliers_available) as avg_alternatives_per_product
# MAGIC     FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_supplier_cost_benchmark
# MAGIC     GROUP BY wholesalerkey
# MAGIC )
# MAGIC SELECT 
# MAGIC     supplier_id,
# MAGIC     products_supplied,
# MAGIC     purchase_transactions,
# MAGIC     total_units_purchased,
# MAGIC     ROUND(avg_cost_per_unit, 2) as avg_cost_per_unit,
# MAGIC     ROUND(total_spend, 2) as total_spend,
# MAGIC     ROUND(avg_cost_variance_pct, 2) as cost_variance_pct,
# MAGIC     ROUND(total_potential_savings, 2) as potential_annual_savings,
# MAGIC     risk_level,
# MAGIC     ROUND(avg_alternatives_per_product, 1) as avg_alternatives_available,
# MAGIC     
# MAGIC     -- Performance grade
# MAGIC     CASE 
# MAGIC         WHEN avg_cost_variance_pct <= 0 THEN 'A - COMPETITIVE'
# MAGIC         WHEN avg_cost_variance_pct <= 10 THEN 'B - FAIR'
# MAGIC         WHEN avg_cost_variance_pct <= 25 THEN 'C - EXPENSIVE'
# MAGIC         ELSE 'D - OVERPRICED'
# MAGIC     END as performance_grade,
# MAGIC     
# MAGIC     -- Action recommendation
# MAGIC     CASE 
# MAGIC         WHEN avg_cost_variance_pct > 25 AND avg_alternatives_per_product >= 3 THEN 'RENEGOTIATE_OR_SWITCH'
# MAGIC         WHEN avg_cost_variance_pct > 15 THEN 'NEGOTIATE_PRICING'
# MAGIC         WHEN risk_level = 'HIGH_RISK' THEN 'DIVERSIFY_SUPPLIERS'
# MAGIC         WHEN avg_cost_variance_pct <= 0 THEN 'MAINTAIN_RELATIONSHIP'
# MAGIC         ELSE 'MONITOR'
# MAGIC     END as recommended_action,
# MAGIC     
# MAGIC     current_timestamp() as last_updated
# MAGIC     
# MAGIC FROM supplier_stats
# MAGIC ORDER BY total_potential_savings DESC

# COMMAND ----------

# DBTITLE 1,Create Cost Optimization Opportunities Mart
# MAGIC %sql
# MAGIC -- Prioritized list of cost-saving opportunities
# MAGIC CREATE OR REPLACE TABLE {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_cost_optimization_opportunities AS
# MAGIC WITH ranked_opportunities AS (
# MAGIC     SELECT 
# MAGIC         productkey,
# MAGIC         product_name,
# MAGIC         current_avg_cost,
# MAGIC         COUNT(DISTINCT benchmark_supplier_id) as alternative_count,
# MAGIC         MIN(benchmark_cost) as lowest_benchmark_cost,
# MAGIC         MAX(potential_savings_pct) as max_savings_pct,
# MAGIC         AVG(potential_savings_pct) as avg_savings_pct
# MAGIC     FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_product_sourcing_alternatives
# MAGIC     WHERE savings_opportunity IN ('HIGH_SAVINGS', 'MEDIUM_SAVINGS')
# MAGIC     GROUP BY productkey, product_name, current_avg_cost
# MAGIC ),
# MAGIC purchase_volume AS (
# MAGIC     SELECT 
# MAGIC         productkey,
# MAGIC         SUM(quantity) as annual_volume,
# MAGIC         COUNT(DISTINCT wholesalerkey) as current_supplier_count
# MAGIC     FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.fact_purchases
# MAGIC     GROUP BY productkey
# MAGIC )
# MAGIC SELECT 
# MAGIC     r.productkey,
# MAGIC     r.product_name,
# MAGIC     r.current_avg_cost,
# MAGIC     r.lowest_benchmark_cost,
# MAGIC     ROUND(r.max_savings_pct, 2) as max_savings_pct,
# MAGIC     r.alternative_count,
# MAGIC     pv.annual_volume,
# MAGIC     pv.current_supplier_count,
# MAGIC     
# MAGIC     -- Calculate annual savings potential
# MAGIC     ROUND(
# MAGIC         (r.current_avg_cost - r.lowest_benchmark_cost) * pv.annual_volume,
# MAGIC         2
# MAGIC     ) as estimated_annual_savings,
# MAGIC     
# MAGIC     -- Prioritization score (0-100)
# MAGIC     ROUND(
# MAGIC         (r.max_savings_pct * 0.6) + 
# MAGIC         (LEAST(r.alternative_count / 10.0, 1.0) * 20) +
# MAGIC         (CASE WHEN pv.current_supplier_count = 1 THEN 20 ELSE 0 END),
# MAGIC         1
# MAGIC     ) as optimization_priority_score,
# MAGIC     
# MAGIC     -- Action priority
# MAGIC     CASE 
# MAGIC         WHEN r.max_savings_pct > 30 AND r.alternative_count >= 5 THEN 'CRITICAL'
# MAGIC         WHEN r.max_savings_pct > 20 THEN 'HIGH'
# MAGIC         WHEN r.max_savings_pct > 10 THEN 'MEDIUM'
# MAGIC         ELSE 'LOW'
# MAGIC     END as action_priority,
# MAGIC     
# MAGIC     current_timestamp() as last_updated
# MAGIC     
# MAGIC FROM ranked_opportunities r
# MAGIC JOIN purchase_volume pv ON r.productkey = pv.productkey
# MAGIC ORDER BY optimization_priority_score DESC, estimated_annual_savings DESC
# MAGIC LIMIT 100

# COMMAND ----------

# DBTITLE 1,Executive Summary & Insights
print("="*80)
print("✅ SUPPLIER PERFORMANCE GOLD ANALYTICS COMPLETE")
print("="*80)

# Total potential savings
total_savings = spark.sql(f"""
    SELECT SUM(potential_annual_savings) as total_savings
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_supplier_performance
""").collect()[0]['total_savings']

print(f"\n💰 TOTAL ANNUAL SAVINGS POTENTIAL: ${total_savings:,.2f}")

# Supplier performance distribution
print("\n=== Supplier Performance Distribution ===")
spark.sql(f"""
    SELECT 
        performance_grade,
        COUNT(*) as supplier_count,
        ROUND(SUM(total_spend), 2) as total_spend,
        ROUND(SUM(potential_annual_savings), 2) as potential_savings
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_supplier_performance
    GROUP BY performance_grade
    ORDER BY performance_grade
""").show(truncate=False)

# Top 10 cost optimization opportunities
print("\n=== Top 10 Cost Optimization Opportunities ===")
spark.sql(f"""
    SELECT 
        product_name,
        current_avg_cost,
        lowest_benchmark_cost,
        max_savings_pct,
        estimated_annual_savings,
        action_priority
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_cost_optimization_opportunities
    LIMIT 10
""").show(truncate=False)

# Recommended actions summary
print("\n=== Recommended Actions Summary ===")
spark.sql(f"""
    SELECT 
        recommended_action,
        COUNT(*) as supplier_count,
        ROUND(SUM(potential_annual_savings), 2) as total_savings_opportunity
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_supplier_performance
    GROUP BY recommended_action
    ORDER BY total_savings_opportunity DESC
""").show(truncate=False)

print("\n" + "="*80)
print("Gold Marts Created:")
print(f"  - {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_supplier_performance")
print(f"  - {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_cost_optimization_opportunities")
print("="*80)

# COMMAND ----------

