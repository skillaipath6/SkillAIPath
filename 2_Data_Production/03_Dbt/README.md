# SkillAIPath Data Warehouse - dbt Project

**Version:** 2.0.0 (Production-Ready Architecture)  
**Status:** Production Ready  
**Last Updated:** August 5, 2026

---

## Overview

Enterprise-grade dbt project for the SkillAIPath data warehouse. Implements a medallion architecture (Bronze to Silver to Gold) with clear ownership boundaries, scalable design, and production-ready patterns.

### Key Features

* Single ownership per layer - No duplicate transformations
* Clean folder structure - Standard dbt conventions
* Incremental loading - Efficient data processing
* Dimensional modeling - Star schema in silver layer
* Comprehensive testing - Data quality validation
* Full documentation - Auto-generated lineage and descriptions

---

## Architecture

Bronze (Databricks) - Raw ingestion layer
  Owner: Ingestion
  Tables: bronze.sales, bronze.purchases, etc.
  
Staging (dbt) - Light cleansing, type casting
  Owner: dbt
  Models: stg_sales, stg_customers, etc.
  Schema: staging
  Materialized: view
  
Silver (dbt) - Business logic + dimensional model
  Owner: dbt
  Models: dim_customer, fact_sales, int_*, etc.
  Schema: silver
  Materialized: table (incremental)
  
Gold (dbt) - Business-ready analytics marts
  Owner: dbt
  Models: mart_customer_360, mart_product_*, etc.
  Schema: gold
  Materialized: table

**Clear ownership:**
* **Databricks ingestion** owns Bronze
* **dbt** owns Silver (intermediate) + Gold (marts)

---

## Quick Start

```bash
# 1. Install dependencies
dbt deps

# 2. Compile & check
dbt compile

# 3. Test sources
dbt test --select source:*

# 4. Run all models
dbt run

# 5. Run tests
dbt test

# 6. Generate docs
dbt docs generate
dbt docs serve
```

Full guide: QUICK_START.md

---

## Project Structure

```
03_Dbt/
├── dbt_project.yml              # Project configuration
├── README.md                    # This file
├── QUICK_START.md              # Getting started guide
├── MIGRATION_SUMMARY.md        # Complete refactoring documentation
├── models/
│   ├── staging/                # Layer 1: Bronze to Staging
│   │   ├── _sources.yml       # Bronze source definitions
│   │   ├── schema.yml         # Staging model tests & docs
│   │   ├── stg_sales.sql
│   │   ├── stg_purchases.sql
│   │   ├── stg_stock.sql
│   │   ├── stg_customers.sql
│   │   └── stg_products.sql
│   │
│   ├── intermediate/           # Layer 2: Silver (Dimensional Model)
│   │   ├── schema.yml         # Intermediate model tests & docs
│   │   ├── int_customer_metrics.sql
│   │   ├── int_product_metrics.sql
│   │   ├── int_sales_enriched.sql
│   │   ├── dim_customer.sql   # Customer dimension
│   │   ├── dim_product.sql    # Product dimension
│   │   ├── dim_product_category.sql
│   │   ├── dim_warehouse.sql  # Warehouse dimension
│   │   ├── dim_date.sql       # Date dimension
│   │   ├── fact_sales.sql     # Sales fact (incremental)
│   │   └── fact_inventory.sql # Inventory fact
│   │
│   └── marts/                  # Layer 3: Gold (Business Marts)
│       ├── schema.yml         # Mart model tests & docs
│       ├── mart_customer_360.sql
│       ├── mart_product_performance.sql
│       └── mart_inventory_health.sql
```

---

## Model Inventory

### 18 Total Models

#### Staging (5 models)
Views that cleanse and standardize bronze data.

* stg_sales - Sales transactions
* stg_purchases - Purchase orders
* stg_stock - Inventory snapshots
* stg_customers - Customer master
* stg_products - Product master

#### Intermediate (10 models)
Tables that implement business logic and dimensional modeling.

**Enrichment Models:**
* int_customer_metrics - Customer aggregations
* int_product_metrics - Product aggregations
* int_sales_enriched - Sales with context

**Dimensional Model (Silver Layer):**
* dim_customer - Customer dimension (SCD Type 1)
* dim_product - Product dimension
* dim_product_category - Category dimension
* dim_warehouse - Warehouse dimension
* dim_date - Date dimension
* fact_sales - Sales fact (incremental)
* fact_inventory - Inventory fact

#### Marts (3 models)
Business-ready gold layer tables for analytics.

* mart_customer_360 - Customer lifetime value & segmentation
* mart_product_performance - Product sales & profitability
* mart_inventory_health - Stock levels & turnover

---

## Key Improvements from v1.0

| Aspect | Before (v1.0) | After (v2.0) |
|--------|---------------|--------------|
| **Folder structure** | Nested _extracted folders | Clean staging/intermediate/marts |
| **Silver ownership** | PySpark AND dbt (conflict) | dbt only (single owner) |
| **Mart dependencies** | source('silver', ...) external | ref('dim_*', 'fact_*') dbt models |
| **Incremental bugs** | NULL watermark breaks first run | COALESCE handles NULL correctly |
| **Ephemeral models** | Can't test int_customer_metrics | All models testable (view/table) |
| **Schema changes** | Break incremental models | on_schema_change='append_new_columns' |
| **Source names** | bronze.stg_sales (wrong) | bronze.sales (correct) |
| **Inter-dependencies** | Staging refs other staging | Staging only refs sources |
| **Global configs** | unique_key='SalesID' for all | Each model defines own key |
| **Bronze in dbt** | Bronze config in dbt_project.yml | Removed (bronze is external) |

Full details: MIGRATION_SUMMARY.md

---

## Testing

### Source Tests
```bash
dbt test --select source:*
```
Verifies bronze tables exist and meet expectations.

### Model Tests
```bash
dbt test --select staging      # Staging layer
dbt test --select intermediate # Intermediate layer
dbt test --select marts        # Marts layer
```

### Test Types
* **Unique:** Primary keys are unique
* **Not Null:** Required fields are populated
* **Relationships:** Foreign keys are valid
* **Accepted Values:** Enums match expected values

---

## Prerequisites

* Databricks workspace with SQL warehouse
* Bronze tables exist:
  * bronze.sales
  * bronze.purchases
  * bronze.inventory
* dbt Core 1.5+ or dbt Cloud
* dbt-databricks adapter
* Python 3.8+

---

## Support & Documentation

* Quick Start: QUICK_START.md
* Migration Details: MIGRATION_SUMMARY.md
* Interactive Docs: Run dbt docs serve
* Official dbt Docs: https://docs.getdbt.com/

---

## Roadmap

### Completed (v2.0)
* Production-ready architecture
* Single ownership per layer
* Incremental loading
* Dimensional modeling
* Comprehensive testing

### Planned (v2.1)
* Add SCD Type 2 tracking for customer dimension
* Create snapshot tables for audit trail
* Add more custom business logic tests
* Implement data freshness checks
* Expand mart layer with new business requirements

### Technical Debt
* Rename bronze tables (remove stg_ prefix) - coordination with PySpark team
* Add true master data sources for customers/products (currently derived from transactions)
* Improve product category logic (currently keyword-based)



---

## Macros

**Status:** No custom macros - all inherited from dbt_utils package

**Removed Macros** (available in backup_before_refactor/ if needed):
* audit_columns.sql - Generates audit columns
* calculate_growth.sql - Calculates percentage growth
* fiscal_year.sql - Calculates Indian fiscal year
* format_currency.sql - Formats numbers as INR currency

All removed macros were unused in production models.

---

**Maintained by:** Data Engineering Team  
**Project Owner:** SkillAIPath  
**Version:** 2.0.0  
**Last Updated:** August 5, 2026
