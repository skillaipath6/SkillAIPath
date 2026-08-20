# Data Platform Foundation Guide
## Medallion Architecture | Bronze → Silver → Gold

Complete data platform with medallion architecture, 13 dimensions, 10 facts, streaming CDC, dbt transformations, and gold-layer analytics.

---

## Quick Navigation

**[Architecture Diagrams](#architecture)**  
**[Components](#components)**  
**[Quick Starts](#quick-starts)**

---

## Architecture

Explore visual flow diagrams for the data platform:

* **[Medallion Complete Architecture](Architecture_Diagrams/Medallion_Complete_Architecture.md)** — Bronze → Silver → Gold layers with star schema
* **[Streaming CDC Pipeline](Architecture_Diagrams/Streaming_CDC_Pipeline.md)** — Real-time change data capture with checkpointing
* **[dbt Transformation DAG](Architecture_Diagrams/Dbt_Transformation_DAG.md)** — Source → Staging → Marts with testing

---

## Components

### 01_Bronze_Ingestion
**Purpose:** Raw data ingestion from all sources  
**Pattern:** Auto Loader with schema inference  
**Output:** 14 Bronze tables (timestamped, audit trail)  
**Quick Start:** Configure Auto Loader for your cloud storage

### 02_Medallion_Architecture
**Purpose:** Bronze → Silver → Gold transformations

#### 01_Dimensions (13 tables)
* dim_customers (SCD Type 2)
* dim_products
* dim_locations
* dim_employees
* dim_time
* + 8 more domain dimensions

#### 02_Facts (10 tables)
* fact_sales
* fact_inventory
* fact_orders
* fact_shipments
* fact_returns
* + 5 more transactional facts

#### 03_Streaming_Cdc
* Real-time change data capture
* Structured Streaming with watermarking
* MERGE INTO for upsert logic
* Checkpointing for fault tolerance

#### 04_Gold
* Aggregated business metrics
* Pre-joined star schema
* Report-ready tables
* OLAP cube structures

#### 05_Gold_Views
* Materialized views for performance
* Business-specific aggregations
* Self-service BI layers

### 03_Dbt
**Purpose:** SQL-based transformations with testing  
**Models:** 50+ across staging/intermediate/marts  
**Tests:** 200+ schema and data tests  
**Quick Start:** `dbt run` to execute all models

---

## Quick Starts

### Deploy Bronze Layer
1. Configure Auto Loader for your cloud storage
2. Run `01_Bronze_Ingestion/setup.py`
3. Verify 14 Bronze tables created
4. Check data lineage in Unity Catalog

### Implement SCD Type 2
1. Review `02_Medallion_Architecture/01_Dimensions/dim_customers.py`
2. Customize for your business keys
3. Run dimension processing
4. Validate valid_from/valid_to dates

### Setup Streaming CDC
1. Configure Kafka/Kinesis source
2. Run `03_Streaming_Cdc/cdc_pipeline.py`
3. Monitor checkpoint progress
4. Verify MERGE operations

### Run dbt Transformations
```bash
cd 03_Dbt
dbt deps  # Install dependencies
dbt run   # Execute all models
dbt test  # Run data quality tests
dbt docs generate  # Create documentation
dbt docs serve     # View lineage DAG
```

---

## Performance Optimization

| Optimization | Implementation | Impact |
|-------------|----------------|--------|
| Z-ordering | OPTIMIZE table ZORDER BY (join_key) | -50% query time |
| Partitioning | PARTITION BY (date) | -60% data scanned |
| File compaction | OPTIMIZE table | -40% storage, +30% read speed |
| Liquid clustering | CLUSTER BY (col1, col2) | -50% query time (Gold) |
| Broadcast joins | broadcast(dim_table) | -70% shuffle time |

---

## Data Quality Framework

### Bronze Layer
* Schema validation on ingestion
* Null checks on required fields
* Data type enforcement
* Duplicate detection

### Silver Layer
* SCD Type 2 consistency checks
* Referential integrity (foreign keys)
* Business rule validation
* Anomaly detection

### Gold Layer
* Aggregation correctness tests
* Historical trend validation
* Report reconciliation
* Cross-table consistency

---

## Module Statistics

* **Bronze Tables:** 14 (raw ingestion)
* **Silver Dimensions:** 13 (SCD Type 2)
* **Silver Facts:** 10 (incremental merge)
* **Gold Views:** 20+ (business metrics)
* **dbt Models:** 50+ (staging/intermediate/marts)
* **dbt Tests:** 200+ (schema & data quality)

---

**Module:** 2_Data_Production  
**Pattern:** Medallion Architecture  
**Status:** Production-ready  
**Last Updated:** January 2025
