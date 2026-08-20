-- dbt Intermediate Model: Sales Fact Table
-- Core sales transactions with dimensional surrogate keys

{{
  config(
    materialized='incremental',
    unique_key='OrderID',
    incremental_strategy='merge',
    on_schema_change='append_new_columns',
    tags=['intermediate', 'fact', 'sales']
  )
}}

WITH sales_data AS (
  SELECT
    s.OrderID,
    s.OrderDate,
    s.MFDDate,
    s.EXPDate,
    s.DeliveryDate,
    s.CustomerName,
    s.ProductName,
    s.ProductCategory,
    s.WareHouseName,
    s.RetailerName,
    s.AgentName,
    s.PaymentMode,
    s.ProductQuantity,
    s.CostPrice,
    s.SellingPrice,
    s.Discount,
    s.FinalPrice,
    s.CGST,
    s.SGST,
    s.BatchDate,
    s.LoadedAt
  FROM {{ ref('stg_sales') }} s
  {% if is_incremental() %}
  WHERE s.LoadedAt > (
    SELECT COALESCE(MAX(LoadedAt), TIMESTAMP'1900-01-01 00:00:00')
    FROM {{ this }}
  )
  {% endif %}
),

dimension_keys AS (
  SELECT
    CAST(s.OrderID AS BIGINT) AS OrderID,
    COALESCE(c.CustomerSK, -1) AS CustomerSK,
    COALESCE(p.ProductSK, -1) AS ProductSK,
    COALESCE(w.WareHouseSK, -1) AS WarehouseSK,
    COALESCE(r.RetailerSK, -1) AS RetailerSK,
    COALESCE(a.AgentSK, -1) AS AgentSK,
    COALESCE(pm.PaymentModeSK, -1) AS PaymentModeSK,
    COALESCE(pc.ProductCategorySK, -1) AS ProductCategorySK,
    COALESCE(d1.DateID, -1) AS OrderDateID,
    COALESCE(d2.DateID, -1) AS MFDDateID,
    COALESCE(d3.DateID, -1) AS EXPDateID,
    COALESCE(d4.DateID, -1) AS DeliveryDateID,
    s.ProductQuantity,
    CAST(s.CostPrice AS DECIMAL(10,2)) AS CostPrice,
    CAST(s.SellingPrice AS DECIMAL(10,2)) AS sellingPrice,
    CAST(s.Discount AS DECIMAL(10,2)) AS discount,
    CAST(s.FinalPrice AS DECIMAL(10,2)) AS finalprice,
    CAST(s.CGST AS DECIMAL(10,2)) AS CGST,
    CAST(s.SGST AS DECIMAL(10,2)) AS SGST,
    s.BatchDate,
    s.LoadedAt
  FROM sales_data s
  LEFT JOIN {{ ref('dim_customer') }} c 
    ON s.CustomerName = c.CustomerName
  LEFT JOIN {{ ref('dim_product') }} p 
    ON s.ProductName = p.ProductName
  LEFT JOIN {{ ref('dim_product_category') }} pc 
    ON s.ProductCategory = pc.ProductCategory
  LEFT JOIN {{ ref('dim_warehouse') }} w 
    ON s.WareHouseName = w.WareHouseName
  LEFT JOIN {{ ref('dim_retailer') }} r 
    ON s.RetailerName = r.RetailerName
  LEFT JOIN {{ ref('dim_agent') }} a 
    ON s.AgentName = a.AgentName
  LEFT JOIN {{ ref('dim_payment_mode') }} pm 
    ON s.PaymentMode = pm.PaymentMode
  LEFT JOIN {{ ref('dim_date') }} d1 
    ON s.OrderDate = d1.Date
  LEFT JOIN {{ ref('dim_date') }} d2 
    ON s.MFDDate = d2.Date
  LEFT JOIN {{ ref('dim_date') }} d3 
    ON s.EXPDate = d3.Date
  LEFT JOIN {{ ref('dim_date') }} d4 
    ON s.DeliveryDate = d4.Date
)

SELECT * FROM dimension_keys
