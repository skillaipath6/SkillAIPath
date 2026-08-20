# Medallion Complete Architecture
## Bronze → Silver → Gold | Delta Lake | SCD Type 2

Complete medallion architecture with 13 dimensions, 10 facts, streaming CDC, and gold aggregations.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│            MEDALLION ARCHITECTURE: BRONZE ─> SILVER ─> GOLD                │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                                             │
├──────────────────────────────────────────────────────────────────────────┤
│  Cloud Storage (CSV/JSON/Parquet) | Kafka/Kinesis (Real-time)            │
│  REST APIs (External Systems)                                            │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────┴─────────────────────────────────────┐
│  BRONZE LAYER (Raw, Timestamped, 14 Tables)                              │
├──────────────────────────────────────────────────────────────────────────┤
│  Auto Loader (Schema Inference) ─> Bronze Tables (Timestamped)          │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────┴─────────────────────────────────────┐
│  SILVER LAYER (Cleansed, 23 Tables)                                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  13 Dimensions (SCD Type 2)                                              │
│  • dim_customers, dim_products, dim_locations, dim_employees           │
│  • dim_time (date, week, month, quarter, year) + 8 more                │
│                                                                          │
│  10 Facts (Incremental Merge)                                            │
│  • fact_sales, fact_inventory, fact_orders, fact_shipments             │
│  • fact_returns + 5 more transactional facts                           │
│                                                                          │
│  Streaming CDC (Change Tracking)                                         │
│  • Insert/Update/Delete operations                                      │
│  • Watermarking, Checkpointing                                         │
│                                                                          │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────┴─────────────────────────────────────┐
│  GOLD LAYER (Business-Ready, Optimized)                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Star Schema (OLAP Ready) ─> Aggregated KPIs ─> Materialized Views    │
│                                                                          │
│  • Pre-joined dimensions + facts                                        │
│  • Report-ready tables                                                 │
│  • OLAP cube structures                                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Layers

### Bronze Layer
* Raw data from all sources
* Schema-on-read with Auto Loader
* Timestamped for audit trail
* No transformations applied
* 14 tables total

### Silver Layer - Dimensions (13)
* dim_customers - SCD Type 2
* dim_products
* dim_locations
* dim_employees
* dim_time (date, week, month, quarter, year)
* + 8 more domain dimensions
* Slowly changing dimension tracking
* Business key + surrogate key
* Valid_from and valid_to dates

### Silver Layer - Facts (10)
* fact_sales
* fact_inventory
* fact_orders
* fact_shipments
* fact_returns
* + 5 more transactional facts
* Incremental merge from Bronze
* Foreign keys to dimension tables

### Silver Layer - CDC
* Real-time change data capture
* Insert/Update/Delete operations
* Watermarking for late data
* Checkpointing for recovery

### Gold Layer
* Aggregated business metrics
* Pre-joined star schema
* Materialized views for performance
* Report-ready tables
* OLAP cube structures

## Performance Optimizations

* Z-ordering on join keys
* Partitioning by date
* Delta Lake file compaction
* Liquid clustering (Gold layer)
* Broadcast joins for dimensions

Module: 2_Data_Production
Layers: Bronze → Silver → Gold
Tables: 14 Bronze + 23 Silver + Gold views
Last Updated: January 2025
