-- dbt Intermediate Model: Purchase Fact Table
-- Core purchase transactions with dimensional surrogate keys

{{
  config(
    materialized='incremental',
    unique_key='PurchaseID',
    incremental_strategy='merge',
    on_schema_change='append_new_columns',
    tags=['intermediate', 'fact', 'purchase']
  )
}}

WITH purchase_data AS (
  SELECT
    CAST(PurchaseID AS BIGINT) AS PurchaseID,
    ProductName,
    WareHouseName,
    WholeSalerName,
    CAST(PurchaseDate AS DATE) AS PurchaseDate,
    Quantity,
    UnitCost,
    NetAmount,
    LoadedAt
  FROM {{ source('bronze', 'purchases') }}
  {% if is_incremental() %}
  WHERE LoadedAt > (
    SELECT COALESCE(MAX(LoadedAt), TIMESTAMP'1900-01-01 00:00:00')
    FROM {{ this }}
  )
  {% endif %}
),

dimension_keys AS (
  SELECT
    p.PurchaseID,
    COALESCE(prod.ProductSK, -1) AS ProductSK,
    COALESCE(w.WareHouseSK, -1) AS WarehouseSK,
    COALESCE(ws.WholeSalerSK, -1) AS WholesalerSK,
    COALESCE(d.DateID, -1) AS PurchaseDateID,
    p.Quantity,
    CAST(p.UnitCost AS DECIMAL(10,2)) AS UnitCost,
    CAST(p.NetAmount AS DECIMAL(10,2)) AS NetAmount,
    p.PurchaseDate,
    p.LoadedAt
  FROM purchase_data p
  LEFT JOIN {{ ref('dim_product') }} prod 
    ON p.ProductName = prod.ProductName
  LEFT JOIN {{ ref('dim_warehouse') }} w 
    ON p.WareHouseName = w.WareHouseName
  LEFT JOIN {{ ref('dim_wholesaler') }} ws 
    ON p.WholeSalerName = ws.WholeSalerName
  LEFT JOIN {{ ref('dim_date') }} d 
    ON p.PurchaseDate = d.Date
)

SELECT * FROM dimension_keys
