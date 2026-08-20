# Databricks notebook source
# DBTITLE 1,Enrichment Pipeline Orchestrator - COMPLETE BRONZE INGESTION
# MAGIC %md
# MAGIC # External Enrichment Pipeline - Complete Orchestrator
# MAGIC
# MAGIC **Purpose:** Orchestrate all bronze-layer enrichment data ingestion
# MAGIC
# MAGIC **Pipeline Stages:**
# MAGIC 1. **Supplier Network** (100K+ suppliers, 50K+ parts, 500K+ relationships)
# MAGIC 2. **Weather Data** (55K+ daily weather records, 30 cities, 5 years)
# MAGIC 3. **Exchange Rates & Commodities** (73K+ FX/commodity prices, 5 years)
# MAGIC 4. **Logistics Deliveries** (500K+ delivery transactions, 2 years)
# MAGIC
# MAGIC **Total Volume:** ~1.3 Million enrichment records
# MAGIC
# MAGIC **Schema Convention:** All bronze tables use `sap_dev.bronze.ext_*` naming
# MAGIC
# MAGIC **Execution:** Run all cells sequentially or use Databricks Workflows

# COMMAND ----------

# DBTITLE 1,Load Config
%run ../../1_Canvas/1_Setup/1_config

# COMMAND ----------

# DBTITLE 1,Import Libraries
from pyspark.sql import functions as F
from datetime import datetime

print("="*80)
print("ENRICHMENT PIPELINE ORCHESTRATOR - PRODUCTION-GRADE")
print("="*80)
print(f"Target Catalog: {Config.CATALOG}")
print(f"Target Schema: {Config.SCHEMA_BRONZE}")
print(f"Timestamp: {datetime.now()}")
print("="*80)

# COMMAND ----------

# DBTITLE 1,STAGE 1: Ingest Supplier Network (100K+ Suppliers)
print("\n" + "="*80)
print("STAGE 1: SUPPLIER NETWORK INGESTION")
print("="*80)
print("Executing: 01_ingest_tpch_suppliers.py")
print("Expected Output: ~650K records (suppliers + parts + relationships)")
print("="*80)

%run ./01_ingest_tpch_suppliers

print("\n✅ STAGE 1 COMPLETE")
supplier_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_suppliers").count()
parts_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_parts").count()
partsupp_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_partsupp").count()
print(f"Suppliers: {supplier_count:,}")
print(f"Parts: {parts_count:,}")
print(f"Relationships: {partsupp_count:,}")
print(f"Total: {supplier_count + parts_count + partsupp_count:,}")

# COMMAND ----------

# DBTITLE 1,STAGE 2: Ingest Weather Data (55K+ Records)
print("\n" + "="*80)
print("STAGE 2: WEATHER DATA INGESTION")
print("="*80)
print("Executing: 02_ingest_weather_data.py")
print("Expected Output: ~55K records (30 cities × 5 years × 365 days)")
print("="*80)

%run ./02_ingest_weather_data

print("\n✅ STAGE 2 COMPLETE")
weather_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_weather_daily").count()
print(f"Weather Records: {weather_count:,}")

# COMMAND ----------

# DBTITLE 1,STAGE 3: Ingest Exchange Rates & Commodities (73K+ Records)
print("\n" + "="*80)
print("STAGE 3: EXCHANGE RATES & COMMODITIES INGESTION")
print("="*80)
print("Executing: 07_ingest_exchange_rates.py")
print("Expected Output: ~73K records (30 FX + 10 commodities × 5 years)")
print("="*80)

%run ./07_ingest_exchange_rates

print("\n✅ STAGE 3 COMPLETE")
fx_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_exchange_rates").count()
print(f"FX & Commodity Records: {fx_count:,}")

# COMMAND ----------

# DBTITLE 1,STAGE 4: Ingest Logistics Deliveries (500K+ Records)
print("\n" + "="*80)
print("STAGE 4: LOGISTICS DELIVERIES INGESTION")
print("="*80)
print("Executing: 08_ingest_logistics.py")
print("Expected Output: ~500K records (Indian delivery transactions, 2 years)")
print("="*80)

%run ./08_ingest_logistics

print("\n✅ STAGE 4 COMPLETE")
logistics_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_logistics_deliveries").count()
print(f"Logistics Records: {logistics_count:,}")

# COMMAND ----------

# DBTITLE 1,Pipeline Summary & Validation
print("\n" + "="*80)
print("✅ ENRICHMENT PIPELINE COMPLETE - ALL STAGES SUCCESSFUL")
print("="*80)

# Calculate totals
total_supplier_network = supplier_count + parts_count + partsupp_count
total_all = total_supplier_network + weather_count + fx_count + logistics_count

print(f"\n📊 INGESTION SUMMARY:")
print(f"  Stage 1 - Supplier Network:  {total_supplier_network:>10,} records")
print(f"  Stage 2 - Weather Data:      {weather_count:>10,} records")
print(f"  Stage 3 - FX & Commodities:  {fx_count:>10,} records")
print(f"  Stage 4 - Logistics:         {logistics_count:>10,} records")
print(f"  " + "-"*40)
print(f"  TOTAL ENRICHMENT RECORDS:    {total_all:>10,}")

print(f"\n📁 BRONZE TABLES CREATED:")
print(f"  {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_suppliers")
print(f"  {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_parts")
print(f"  {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_tpch_partsupp")
print(f"  {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_weather_daily")
print(f"  {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_exchange_rates")
print(f"  {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_logistics_deliveries")

print(f"\n⏱️  Pipeline Completed: {datetime.now()}")
print(f"\n💡 NEXT STEPS:")
print(f"  1. Run Silver layer notebooks (03_silver_supplier_benchmark.py, etc.)")
print(f"  2. Run Gold layer notebooks (05_gold_supplier_analytics.py, etc.)")
print(f"  3. Schedule this orchestrator as Databricks Job (daily/weekly refresh)")
print(f"  4. Set up quality monitoring and alerting")
print("="*80)

# COMMAND ----------

# DBTITLE 1,Data Quality Validation
print("\n🔍 DATA QUALITY VALIDATION:")

# Check for nulls in key columns
print("\n1. Checking for null values in key fields...")
for table in ["ext_tpch_suppliers", "ext_weather_daily", "ext_exchange_rates", "ext_logistics_deliveries"]:
    df = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.{table}")
    row_count = df.count()
    null_checks = []
    
    # Get first few columns to check
    cols_to_check = df.columns[:5]
    for col in cols_to_check:
        null_count = df.filter(F.col(col).isNull()).count()
        if null_count > 0:
            null_checks.append(f"{col}: {null_count}")
    
    if null_checks:
        print(f"  ⚠️  {table}: {', '.join(null_checks)}")
    else:
        print(f"  ✅ {table}: No nulls in key columns")

# Check date ranges
print("\n2. Validating date ranges...")
weather_dates = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_weather_daily") \
    .agg(F.min("weather_date").alias("min"), F.max("weather_date").alias("max")).collect()[0]
print(f"  Weather: {weather_dates['min']} to {weather_dates['max']}")

fx_dates = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_exchange_rates") \
    .agg(F.min("rate_date").alias("min"), F.max("rate_date").alias("max")).collect()[0]
print(f"  FX/Commodities: {fx_dates['min']} to {fx_dates['max']}")

logistics_dates = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_logistics_deliveries") \
    .agg(F.min("order_date").alias("min"), F.max("order_date").alias("max")).collect()[0]
print(f"  Logistics: {logistics_dates['min']} to {logistics_dates['max']}")

print("\n✅ DATA QUALITY VALIDATION COMPLETE")

# COMMAND ----------

