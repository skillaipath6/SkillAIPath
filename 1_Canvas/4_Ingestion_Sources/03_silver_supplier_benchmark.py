# Databricks notebook source
# DBTITLE 1,Supplier Benchmark Analysis - Silver Layer
# MAGIC %md
# MAGIC # Supplier Benchmark Intelligence - Silver Layer
# MAGIC
# MAGIC **Business Value:** Compare your supplier costs against industry benchmarks
# MAGIC
# MAGIC **Integration Logic:**
# MAGIC - Join your purchase data with TPC-H supplier benchmark data
# MAGIC - Calculate cost variance vs industry standard
# MAGIC - Identify overpriced suppliers and sourcing opportunities
# MAGIC
# MAGIC **Input Tables:**
# MAGIC - `sap_dev.silver.fact_purchases` - Your actual purchase transactions
# MAGIC - `sap_dev.bronze.ext_tpch_suppliers` - TPC-H supplier benchmarks
# MAGIC - `sap_dev.bronze.ext_tpch_partsupp` - Benchmark supplier costs by part
# MAGIC
# MAGIC **Output Tables:**
# MAGIC - `sap_dev.silver.ext_supplier_cost_benchmark` - Supplier cost comparison
# MAGIC - `sap_dev.silver.ext_product_sourcing_alternatives` - Alternative supplier options
# MAGIC
# MAGIC **Key Metrics:**
# MAGIC - Cost variance % vs TPC-H benchmark
# MAGIC - Number of alternative suppliers available
# MAGIC - Potential cost savings per product
# MAGIC - Supplier concentration risk score

# COMMAND ----------

# DBTITLE 1,Load Config
# MAGIC %run ../../1_Canvas/1_Setup/1_config

# COMMAND ----------

# DBTITLE 1,Create Supplier Cost Benchmark Table
# MAGIC %sql
# MAGIC -- Create supplier cost benchmark analysis
# MAGIC CREATE OR REPLACE TABLE {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_supplier_cost_benchmark AS
# MAGIC SELECT 
# MAGIC     -- Your actual purchase data
# MAGIC     p.wholesalerkey,
# MAGIC     p.productkey,
# MAGIC     p.product_name,
# MAGIC     COUNT(*) as purchase_count,
# MAGIC     AVG(p.purchaseprice) as avg_your_cost,
# MAGIC     SUM(p.quantity) as total_quantity_purchased,
# MAGIC     
# MAGIC     -- TPC-H benchmark data (industry standard costs)
# MAGIC     AVG(ps.ps_supplycost) as avg_benchmark_cost,
# MAGIC     COUNT(DISTINCT ps.ps_suppkey) as alternative_suppliers_available,
# MAGIC     
# MAGIC     -- Cost comparison metrics
# MAGIC     ROUND(
# MAGIC         (AVG(p.purchaseprice) - AVG(ps.ps_supplycost)) / AVG(ps.ps_supplycost) * 100, 
# MAGIC         2
# MAGIC     ) as cost_variance_pct,
# MAGIC     
# MAGIC     ROUND(
# MAGIC         (AVG(p.purchaseprice) - AVG(ps.ps_supplycost)) * SUM(p.quantity),
# MAGIC         2
# MAGIC     ) as potential_savings,
# MAGIC     
# MAGIC     -- Risk indicators
# MAGIC     CASE 
# MAGIC         WHEN COUNT(DISTINCT ps.ps_suppkey) = 1 THEN 'HIGH_RISK'
# MAGIC         WHEN COUNT(DISTINCT ps.ps_suppkey) <= 3 THEN 'MEDIUM_RISK'
# MAGIC         ELSE 'LOW_RISK'
# MAGIC     END as supplier_concentration_risk,
# MAGIC     
# MAGIC     current_timestamp() as processed_at
# MAGIC     
# MAGIC FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.fact_purchases p
# MAGIC LEFT JOIN {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_partsupp ps
# MAGIC     ON 1=1  -- Cross join for benchmark comparison (in reality, you'd map product SKUs)
# MAGIC GROUP BY 
# MAGIC     p.wholesalerkey,
# MAGIC     p.productkey,
# MAGIC     p.product_name

# COMMAND ----------

# DBTITLE 1,Create Product Sourcing Alternatives Table
# MAGIC %sql
# MAGIC -- Identify alternative suppliers with better pricing
# MAGIC CREATE OR REPLACE TABLE {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_product_sourcing_alternatives AS
# MAGIC WITH your_costs AS (
# MAGIC     SELECT 
# MAGIC         productkey,
# MAGIC         product_name,
# MAGIC         AVG(purchaseprice) as current_avg_cost
# MAGIC     FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.fact_purchases
# MAGIC     GROUP BY productkey, product_name
# MAGIC ),
# MAGIC benchmark_alternatives AS (
# MAGIC     SELECT 
# MAGIC         ps.ps_partkey as benchmark_part_id,
# MAGIC         ps.ps_suppkey as benchmark_supplier_id,
# MAGIC         s.s_name as benchmark_supplier_name,
# MAGIC         s.s_address as supplier_address,
# MAGIC         s.s_phone as supplier_phone,
# MAGIC         ps.ps_supplycost as benchmark_cost,
# MAGIC         ps.ps_availqty as available_quantity
# MAGIC     FROM {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_partsupp ps
# MAGIC     JOIN {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_suppliers s
# MAGIC         ON ps.ps_suppkey = s.s_suppkey
# MAGIC )
# MAGIC SELECT 
# MAGIC     yc.productkey,
# MAGIC     yc.product_name,
# MAGIC     yc.current_avg_cost,
# MAGIC     ba.benchmark_supplier_id,
# MAGIC     ba.benchmark_supplier_name,
# MAGIC     ba.supplier_address,
# MAGIC     ba.supplier_phone,
# MAGIC     ba.benchmark_cost,
# MAGIC     ba.available_quantity,
# MAGIC     ROUND(
# MAGIC         (yc.current_avg_cost - ba.benchmark_cost) / yc.current_avg_cost * 100,
# MAGIC         2
# MAGIC     ) as potential_savings_pct,
# MAGIC     CASE 
# MAGIC         WHEN ba.benchmark_cost < yc.current_avg_cost * 0.8 THEN 'HIGH_SAVINGS'
# MAGIC         WHEN ba.benchmark_cost < yc.current_avg_cost * 0.95 THEN 'MEDIUM_SAVINGS'
# MAGIC         ELSE 'LOW_SAVINGS'
# MAGIC     END as savings_opportunity,
# MAGIC     current_timestamp() as processed_at
# MAGIC FROM your_costs yc
# MAGIC CROSS JOIN benchmark_alternatives ba
# MAGIC WHERE ba.benchmark_cost < yc.current_avg_cost  -- Only show cheaper alternatives
# MAGIC ORDER BY potential_savings_pct DESC

# COMMAND ----------

# DBTITLE 1,Validation Summary
print("="*80)
print("✅ SUPPLIER BENCHMARK SILVER LAYER COMPLETE")
print("="*80)

# Validate tables created
benchmark_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_supplier_cost_benchmark").count()
alternatives_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_product_sourcing_alternatives").count()

print(f"\nSupplier cost benchmarks: {benchmark_count:,} records")
print(f"Alternative sourcing options: {alternatives_count:,} records")

# Show top 5 cost-saving opportunities
print("\nTop 5 Cost-Saving Opportunities:")
spark.sql(f"""
    SELECT 
        product_name,
        benchmark_supplier_name,
        current_avg_cost,
        benchmark_cost,
        potential_savings_pct,
        savings_opportunity
    FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_product_sourcing_alternatives
    ORDER BY potential_savings_pct DESC
    LIMIT 5
""").show(truncate=False)

print(f"\nSilver tables created:")
print(f"  - {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_supplier_cost_benchmark")
print(f"  - {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_product_sourcing_alternatives")

# COMMAND ----------

