# dbt Transformation DAG Architecture
## Source → Staging → Marts | Testing | Documentation

dbt transformation pipeline with dependency management and data quality tests.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   DBT TRANSFORMATION DAG ARCHITECTURE                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  SOURCE LAYER (sources.yml)                                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│  Bronze Delta Tables | External Systems                                       │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────┴───────────────────────────────────────┐
│  STAGING LAYER (models/staging/) - Materialized as Views                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  stg_customers (Cleansing) | stg_orders (Type Casting)                       │
│  stg_products (Deduplication)                                                │
│                                                                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────┴───────────────────────────────────────┐
│  INTERMEDIATE LAYER (models/intermediate/) - Incremental Models              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  int_orders_enriched (Multi-table Joins)                                     │
│  int_customer_metrics (Aggregations & Complex Calculations)                  │
│                                                                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────┴───────────────────────────────────────┐
│  MARTS LAYER (models/marts/) - Materialized as Tables                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  mart_sales_performance | mart_customer_360 | mart_inventory_health         │
│  (Business-Ready, Pre-Aggregated, Report-Optimized)                         │
│                                                                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────┴───────────────────────────────────────┐
│  TESTING FRAMEWORK (200+ Tests)                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Schema Tests (not_null, unique) | Data Tests (relationships, values)       │
│  Custom SQL Tests                                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## dbt Model Layers

### Source Layer (sources.yml)
* Define Bronze Delta tables
* Document table descriptions
* Configure freshness tests
* Example: bronze.customers, bronze.orders

### Staging Layer (staging/)
* 1:1 with source tables
* Light transformations only
* Cleansing, type casting, renaming
* Deduplication if needed
* Materialized as views

### Intermediate Layer (intermediate/)
* Business logic transformations
* Multi-table joins
* Complex calculations
* Incremental models for performance
* Not exposed to end users

### Marts Layer (marts/)
* Final business-ready tables
* Pre-aggregated metrics
* Report-optimized structures
* Materialized as tables
* Exposed to BI tools

## dbt Features

### Incremental Models
```sql
{{
  config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge'
  )
}}

SELECT *
FROM {{ source('bronze', 'orders') }}
WHERE order_date >= '2024-01-01'

{% if is_incremental() %}
  AND order_date > (SELECT MAX(order_date) FROM {{ this }})
{% endif %}
```

### Testing Framework
* Schema tests: not_null, unique, accepted_values, relationships
* Data tests: custom SQL assertions
* Test on every dbt run
* Fail build on test failures (optional)

### Documentation
* Auto-generated from descriptions
* Data lineage DAG visualization
* Column-level documentation
* Searchable docs site

### Jinja Templating
* Macros for code reuse
* Dynamic SQL generation
* Environment-specific configs
* Custom functions

Module: 2_Data_Production/03_Dbt
Models: 50+ across staging/intermediate/marts
Tests: 200+ schema and data tests
Last Updated: January 2025
