# Databricks notebook source
# DBTITLE 1,Weather-Sales Correlation - Silver Layer
# MAGIC %md
# MAGIC # Weather-Sales Correlation Analysis - Silver Layer
# MAGIC
# MAGIC **Business Value:** Understand weather impact on sales and optimize for seasonal patterns
# MAGIC
# MAGIC **Integration Logic:**
# MAGIC - Join daily sales data with weather conditions
# MAGIC - Calculate weather-driven sales patterns
# MAGIC - Identify seasonal product opportunities
# MAGIC
# MAGIC **Input Tables:**
# MAGIC - `sap_dev.silver.fact_sales` - Daily sales transactions
# MAGIC - `sap_dev.bronze.ext_weather_daily` - Historical weather data
# MAGIC - `sap_dev.silver.dim_product` - Product attributes
# MAGIC - `sap_dev.silver.dim_date` - Date dimension
# MAGIC
# MAGIC **Output Table:**
# MAGIC - `sap_dev.silver.ext_weather_sales_correlation` - Sales enriched with weather context
# MAGIC
# MAGIC **Key Metrics:**
# MAGIC - Sales volume by temperature range
# MAGIC - Revenue correlation with precipitation
# MAGIC - Product performance by weather condition
# MAGIC - Seasonal sales patterns with weather overlay

# COMMAND ----------

# DBTITLE 1,Load Config
# MAGIC %run ../../1_Canvas/1_Setup/1_config

# COMMAND ----------

# DBTITLE 1,Create Weather-Sales Correlation Table
# MAGIC %sql
# MAGIC -- Join sales data with weather conditions
# MAGIC CREATE OR REPLACE TABLE {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation AS
# MAGIC SELECT 
# MAGIC     -- Sales data
# MAGIC     s.saleskey,
# MAGIC     s.datekey,
# MAGIC     s.productkey,
# MAGIC     s.customerkey,
# MAGIC     s.quantity,
# MAGIC     s.finalprice as revenue,
# MAGIC     
# MAGIC     -- Date context
# MAGIC     d.fulldatevalue as sale_date,
# MAGIC     d.monthname,
# MAGIC     d.quartername,
# MAGIC     d.year,
# MAGIC     d.dayofweek,
# MAGIC     d.isweekend,
# MAGIC     
# MAGIC     -- Product context
# MAGIC     p.productname,
# MAGIC     p.subcategory,
# MAGIC     p.category,
# MAGIC     
# MAGIC     -- Weather conditions on sale date
# MAGIC     w.temp_avg_c,
# MAGIC     w.temp_max_c,
# MAGIC     w.temp_min_c,
# MAGIC     w.precipitation_mm,
# MAGIC     w.condition_text as weather_condition,
# MAGIC     w.humidity_avg_pct,
# MAGIC     w.wind_speed_avg_kph,
# MAGIC     
# MAGIC     -- Weather categorization for analysis
# MAGIC     CASE 
# MAGIC         WHEN w.temp_avg_c < 10 THEN 'COLD'
# MAGIC         WHEN w.temp_avg_c < 20 THEN 'MILD'
# MAGIC         WHEN w.temp_avg_c < 30 THEN 'WARM'
# MAGIC         ELSE 'HOT'
# MAGIC     END as temp_category,
# MAGIC     
# MAGIC     CASE 
# MAGIC         WHEN w.precipitation_mm = 0 THEN 'DRY'
# MAGIC         WHEN w.precipitation_mm < 5 THEN 'LIGHT_RAIN'
# MAGIC         WHEN w.precipitation_mm < 20 THEN 'MODERATE_RAIN'
# MAGIC         ELSE 'HEAVY_RAIN'
# MAGIC     END as rain_category,
# MAGIC     
# MAGIC     -- Seasonal indicator
# MAGIC     CASE 
# MAGIC         WHEN d.monthname IN ('December', 'January', 'February') THEN 'WINTER'
# MAGIC         WHEN d.monthname IN ('March', 'April', 'May') THEN 'SPRING'
# MAGIC         WHEN d.monthname IN ('June', 'July', 'August') THEN 'SUMMER'
# MAGIC         ELSE 'FALL'
# MAGIC     END as season,
# MAGIC     
# MAGIC     current_timestamp() as processed_at
# MAGIC     
# MAGIC FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.fact_sales s
# MAGIC JOIN {Config.CATALOG}.{Config.SCHEMA_SILVER}.dim_date d
# MAGIC     ON s.datekey = d.datekey
# MAGIC JOIN {Config.CATALOG}.{Config.SCHEMA_SILVER}.dim_product p
# MAGIC     ON s.productkey = p.productkey
# MAGIC LEFT JOIN {Config.CATALOG}.{Config.SCHEMA_BRONZE}.ext_weather_daily w
# MAGIC     ON d.fulldatevalue = w.weather_date
# MAGIC WHERE w.weather_date IS NOT NULL  -- Only include dates with weather data available

# COMMAND ----------

# DBTITLE 1,Validation & Sample Insights
print("="*80)
print("✅ WEATHER-SALES CORRELATION SILVER LAYER COMPLETE")
print("="*80)

# Validate table created
corr_count = spark.table(f"{Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation").count()
print(f"\nWeather-sales correlation records: {corr_count:,}")

# Show sample insights: Revenue by temperature category
print("\n=== Revenue by Temperature Category ===")
spark.sql(f"""
    SELECT 
        temp_category,
        COUNT(*) as transactions,
        ROUND(SUM(revenue), 2) as total_revenue,
        ROUND(AVG(revenue), 2) as avg_transaction_value,
        ROUND(SUM(quantity), 0) as total_units_sold
    FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation
    GROUP BY temp_category
    ORDER BY total_revenue DESC
""").show()

# Show insights: Revenue by rain category
print("\n=== Revenue by Precipitation Category ===")
spark.sql(f"""
    SELECT 
        rain_category,
        COUNT(*) as transactions,
        ROUND(SUM(revenue), 2) as total_revenue,
        ROUND(AVG(revenue), 2) as avg_transaction_value
    FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation
    GROUP BY rain_category
    ORDER BY total_revenue DESC
""").show()

# Show top products by season
print("\n=== Top Products by Season ===")
spark.sql(f"""
    SELECT 
        season,
        productname,
        ROUND(SUM(revenue), 2) as total_revenue,
        SUM(quantity) as total_units
    FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation
    GROUP BY season, productname
    QUALIFY ROW_NUMBER() OVER (PARTITION BY season ORDER BY SUM(revenue) DESC) <= 3
    ORDER BY season, total_revenue DESC
""").show(truncate=False)

print(f"\nSilver table created:")
print(f"  - {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation")
print(f"\nReady for Gold layer weather impact analytics!")

# COMMAND ----------

