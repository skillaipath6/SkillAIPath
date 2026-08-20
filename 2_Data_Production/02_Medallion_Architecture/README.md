# Medallion Architecture Guide
**58 Production Files** | **Bronze → Silver → Gold** | **Real-Time + Batch**

## 📌 Overview

Complete Medallion (Bronze-Silver-Gold) architecture for retail/e-commerce analytics.

**Files:** 58 Python files across 5 modules  
**Patterns:** SCD0/1/2/3, Full Reload, Upsert, CDC, Streaming  
**Tech:** Delta Lake, Auto Loader, DLT, Lakeflow Connect

## 🏗 Architecture

### 01_Dimensions (14 files)
Master data with SCD patterns:
- **Static (SCD0):** dim_date, dim_product_category, dim_payment_mode
- **SCD1:** dim_customer_scd1 (overwrite)
- **SCD2:** dim_customer_scd2 (history tracking)
- **SCD3:** dim_customer_scd3 (limited history)
- **Others:** dim_warehouse, dim_retailer, dim_agent, dim_product, dim_wholesaler
- **Utility:** pattern_comparison.py

### 02_Facts (10 files)
Transactional + aggregated facts:
- **Core:** fact_sales, fact_purchases, fact_inventory, fact_returns
- **Patterns:** full_reload, upsert, pattern_decision_tree
- **Bridges (M:N):** customer_promotion, product_store, agent_territory

### 03_Streaming_CDC (16 files)
Real-time ingestion:
- **Foundation:** bronze_to_stream_generator, stream_consumer_template, cdc_processor_utility
- **Auto Loader:** streaming_bronze_autoloader, streaming_silver_transforms
- **Patterns:** watermarks, exactly_once, stateful_aggregations, trigger_modes
- **CDC:** customer_scd2_cdc, sales_fact_cdc
- **DLT:** enterprise_dlt_bronze, enterprise_dlt_silver_cdc
- **Lakeflow:** enterprise_lakeflow_connect

### 04_Gold (9 files)
Business marts:
- **Batch:** customer_360, rfm_analysis, product_performance, inventory_health
- **Streaming:** streaming_customer_360, streaming_rfm, streaming_alerts, streaming_product_performance
- **Utility:** dashboard_specification

### 05_Gold_Views (9 files)
Materialized views + optimizations:
- **Views:** daily_sales, product_performance, customer_360, rfm_analysis
- **Advanced:** sql_transactions, multi_table_consistency, partition_optimization, scd_type2_point_in_time

## 🎯 Usage

### Load Customer Dimension (SCD2)
```python
dbutils.notebook.run("01_Dimensions/10_dim_customer_scd2", 1800)
```

### Load Sales Fact (Incremental)
```python
dbutils.notebook.run("02_Facts/06_fact_sales_upsert_pattern", 1800)
```

### Real-Time CDC
```python
dbutils.notebook.run("03_Streaming_CDC/06_customer_scd2_cdc", 0)
```

### Generate Customer 360
```python
dbutils.notebook.run("04_Gold/01_mart_customer_360", 3600)
```

## 📊 Data Flow

```
RAW DATA → DIMENSIONS → FACTS → STREAMING → GOLD → VIEWS → DASHBOARDS
```

## 💡 Patterns

**Full Reload:** Small dimensions (dim_date)  
**SCD1:** Overwrite (dim_customer_scd1)  
**SCD2:** History tracking (dim_customer_scd2)  
**Delta MERGE:** Incremental facts (fact_sales_upsert)  
**CDC Streaming:** Real-time updates (customer_scd2_cdc)

## 🚀 Deployment

**Via Orchestrator:**
```python
dbutils.notebook.run(
    "1_Canvas/2_Orchestration/Data_Platform/1_Data_Platform_Orchestrator",
    14400
)
```

## 📚 Related

- Quality Operations: `../04_Quality_Operations/README.md`
- DBT Integration: `../03_Dbt/`
- Orchestration: `../../1_Canvas/ORCHESTRATION_DAB_GUIDE.md`

✨ **58 files, production-ready!**
