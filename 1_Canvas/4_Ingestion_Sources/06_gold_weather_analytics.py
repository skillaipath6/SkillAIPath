# Databricks notebook source
# DBTITLE 1,Weather Impact Analytics - Gold Layer
# MAGIC %md
# MAGIC # Weather Impact Analytics - Gold Layer
# MAGIC
# MAGIC **Business Value:** Weather-driven sales intelligence and seasonal optimization
# MAGIC
# MAGIC **Analytics Objectives:**
# MAGIC - Quantify weather impact on sales performance
# MAGIC - Identify weather-sensitive products for inventory planning
# MAGIC - Optimize marketing campaigns around weather forecasts
# MAGIC - Build seasonal forecasting models with weather variables
# MAGIC
# MAGIC **Input Tables:**
# MAGIC - `sap_dev.silver.ext_weather_sales_correlation` - Sales + weather data
# MAGIC
# MAGIC **Output Marts:**
# MAGIC - `sap_dev.gold.mart_weather_sales_impact` - Weather impact KPIs
# MAGIC - `sap_dev.gold.mart_weather_sensitive_products` - Product weather sensitivity

# COMMAND ----------

# DBTITLE 1,Load Config
# MAGIC %run ../../1_Canvas/1_Setup/1_config

# COMMAND ----------

# DBTITLE 1,Create Weather Sales Impact Mart
# MAGIC %sql
# MAGIC -- Aggregate weather impact on sales performance
# MAGIC CREATE OR REPLACE TABLE {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sales_impact AS
# MAGIC SELECT 
# MAGIC     -- Weather conditions
# MAGIC     temp_category,
# MAGIC     rain_category,
# MAGIC     season,
# MAGIC     
# MAGIC     -- Sales metrics
# MAGIC     COUNT(*) as total_transactions,
# MAGIC     COUNT(DISTINCT customerkey) as unique_customers,
# MAGIC     SUM(quantity) as total_units_sold,
# MAGIC     ROUND(SUM(revenue), 2) as total_revenue,
# MAGIC     ROUND(AVG(revenue), 2) as avg_transaction_value,
# MAGIC     ROUND(AVG(quantity), 2) as avg_units_per_transaction,
# MAGIC     
# MAGIC     -- Weather-specific insights
# MAGIC     ROUND(AVG(temp_avg_c), 1) as avg_temperature_c,
# MAGIC     ROUND(AVG(precipitation_mm), 2) as avg_precipitation_mm,
# MAGIC     ROUND(AVG(humidity_avg_pct), 1) as avg_humidity_pct,
# MAGIC     
# MAGIC     -- Performance indicators
# MAGIC     ROUND(
# MAGIC         SUM(revenue) / COUNT(*),
# MAGIC         2
# MAGIC     ) as revenue_per_transaction,
# MAGIC     
# MAGIC     ROUND(
# MAGIC         SUM(revenue) / COUNT(DISTINCT sale_date),
# MAGIC         2
# MAGIC     ) as avg_daily_revenue,
# MAGIC     
# MAGIC     -- Comparison to baseline (overall average)
# MAGIC     ROUND(
# MAGIC         (SUM(revenue) / COUNT(*)) / 
# MAGIC         AVG(SUM(revenue) / COUNT(*)) OVER (),
# MAGIC         2
# MAGIC     ) as revenue_index,
# MAGIC     
# MAGIC     current_timestamp() as last_updated
# MAGIC     
# MAGIC FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation
# MAGIC GROUP BY 
# MAGIC     temp_category,
# MAGIC     rain_category,
# MAGIC     season
# MAGIC ORDER BY total_revenue DESC

# COMMAND ----------

# DBTITLE 1,Create Weather-Sensitive Products Mart
# MAGIC %sql
# MAGIC -- Identify products with high weather sensitivity
# MAGIC CREATE OR REPLACE TABLE {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sensitive_products AS
# MAGIC WITH product_weather_stats AS (
# MAGIC     SELECT 
# MAGIC         productkey,
# MAGIC         productname,
# MAGIC         category,
# MAGIC         subcategory,
# MAGIC         temp_category,
# MAGIC         rain_category,
# MAGIC         SUM(quantity) as units_sold,
# MAGIC         ROUND(SUM(revenue), 2) as revenue
# MAGIC     FROM {Config.CATALOG}.{Config.SCHEMA_SILVER}.ext_weather_sales_correlation
# MAGIC     GROUP BY 
# MAGIC         productkey,
# MAGIC         productname,
# MAGIC         category,
# MAGIC         subcategory,
# MAGIC         temp_category,
# MAGIC         rain_category
# MAGIC ),
# MAGIC product_totals AS (
# MAGIC     SELECT 
# MAGIC         productkey,
# MAGIC         productname,
# MAGIC         category,
# MAGIC         subcategory,
# MAGIC         SUM(units_sold) as total_units,
# MAGIC         SUM(revenue) as total_revenue
# MAGIC     FROM product_weather_stats
# MAGIC     GROUP BY productkey, productname, category, subcategory
# MAGIC ),
# MAGIC weather_variance AS (
# MAGIC     SELECT 
# MAGIC         ps.productkey,
# MAGIC         ps.productname,
# MAGIC         ps.category,
# MAGIC         ps.subcategory,
# MAGIC         pt.total_revenue,
# MAGIC         
# MAGIC         -- Temperature sensitivity
# MAGIC         MAX(CASE WHEN ps.temp_category = 'HOT' THEN ps.revenue ELSE 0 END) as revenue_hot,
# MAGIC         MAX(CASE WHEN ps.temp_category = 'COLD' THEN ps.revenue ELSE 0 END) as revenue_cold,
# MAGIC         
# MAGIC         -- Rain sensitivity
# MAGIC         MAX(CASE WHEN ps.rain_category = 'DRY' THEN ps.revenue ELSE 0 END) as revenue_dry,
# MAGIC         MAX(CASE WHEN ps.rain_category IN ('MODERATE_RAIN', 'HEAVY_RAIN') THEN ps.revenue ELSE 0 END) as revenue_rain,
# MAGIC         
# MAGIC         -- Calculate variance as indicator of weather sensitivity
# MAGIC         STDDEV(ps.revenue) as revenue_stddev
# MAGIC         
# MAGIC     FROM product_weather_stats ps
# MAGIC     JOIN product_totals pt ON ps.productkey = pt.productkey
# MAGIC     GROUP BY 
# MAGIC         ps.productkey,
# MAGIC         ps.productname,
# MAGIC         ps.category,
# MAGIC         ps.subcategory,
# MAGIC         pt.total_revenue
# MAGIC )
# MAGIC SELECT 
# MAGIC     productkey,
# MAGIC     productname,
# MAGIC     category,
# MAGIC     subcategory,
# MAGIC     ROUND(total_revenue, 2) as total_revenue,
# MAGIC     ROUND(revenue_stddev, 2) as weather_variance,
# MAGIC     
# MAGIC     -- Weather sensitivity scores (0-100)
# MAGIC     ROUND(
# MAGIC         LEAST((revenue_stddev / NULLIF(total_revenue, 0)) * 100, 100),
# MAGIC         1
# MAGIC     ) as weather_sensitivity_score,
# MAGIC     
# MAGIC     -- Preferred conditions
# MAGIC     CASE 
# MAGIC         WHEN revenue_hot > revenue_cold * 1.5 THEN 'HOT_WEATHER'
# MAGIC         WHEN revenue_cold > revenue_hot * 1.5 THEN 'COLD_WEATHER'
# MAGIC         ELSE 'NEUTRAL'
# MAGIC     END as temperature_preference,
# MAGIC     
# MAGIC     CASE 
# MAGIC         WHEN revenue_rain > revenue_dry * 1.2 THEN 'RAINY_WEATHER'
# MAGIC         WHEN revenue_dry > revenue_rain * 1.2 THEN 'DRY_WEATHER'
# MAGIC         ELSE 'NEUTRAL'
# MAGIC     END as precipitation_preference,
# MAGIC     
# MAGIC     -- Action recommendation
# MAGIC     CASE 
# MAGIC         WHEN revenue_stddev / NULLIF(total_revenue, 0) > 0.3 THEN 'HIGH_SENSITIVITY_FORECAST_CRITICAL'
# MAGIC         WHEN revenue_stddev / NULLIF(total_revenue, 0) > 0.15 THEN 'MODERATE_SENSITIVITY_MONITOR'
# MAGIC         ELSE 'LOW_SENSITIVITY_STANDARD_PLANNING'
# MAGIC     END as inventory_recommendation,
# MAGIC     
# MAGIC     current_timestamp() as last_updated
# MAGIC     
# MAGIC FROM weather_variance
# MAGIC WHERE total_revenue > 0
# MAGIC ORDER BY weather_sensitivity_score DESC
# MAGIC LIMIT 500

# COMMAND ----------

# DBTITLE 1,Weather Impact Insights
print("="*80)
print("✅ WEATHER IMPACT GOLD ANALYTICS COMPLETE")
print("="*80)

# Show weather impact summary
print("\n=== Revenue Performance by Weather Conditions ===")
spark.sql(f"""
    SELECT 
        temp_category,
        rain_category,
        total_transactions,
        total_revenue,
        avg_transaction_value,
        revenue_index
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sales_impact
    ORDER BY total_revenue DESC
    LIMIT 10
""").show(truncate=False)

# Show seasonal performance
print("\n=== Revenue by Season ===")
spark.sql(f"""
    SELECT 
        season,
        SUM(total_transactions) as transactions,
        ROUND(SUM(total_revenue), 2) as revenue,
        ROUND(AVG(avg_transaction_value), 2) as avg_transaction
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sales_impact
    GROUP BY season
    ORDER BY revenue DESC
""").show(truncate=False)

# Show top weather-sensitive products
print("\n=== Top 10 Weather-Sensitive Products ===")
spark.sql(f"""
    SELECT 
        productname,
        category,
        weather_sensitivity_score,
        temperature_preference,
        precipitation_preference,
        inventory_recommendation
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sensitive_products
    ORDER BY weather_sensitivity_score DESC
    LIMIT 10
""").show(truncate=False)

# Count high-sensitivity products
high_sensitivity = spark.sql(f"""
    SELECT COUNT(*) as count
    FROM {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sensitive_products
    WHERE weather_sensitivity_score > 30
""").collect()[0]['count']

print(f"\n⛈️  Weather-Sensitive Products: {high_sensitivity} products require forecast-driven inventory planning")

print("\n" + "="*80)
print("Gold Marts Created:")
print(f"  - {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sales_impact")
print(f"  - {Config.CATALOG}.{Config.SCHEMA_GOLD}.mart_weather_sensitive_products")
print("="*80)

# COMMAND ----------

