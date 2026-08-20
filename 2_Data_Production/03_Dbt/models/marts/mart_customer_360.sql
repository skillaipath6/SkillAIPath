-- dbt Mart Model: Customer 360
-- Combines customer demographics, purchase behavior, and lifetime value
-- Uses dbt intermediate models (single ownership: dbt owns silver layer)

{{
  config(
    materialized='table',
    file_format='delta',
    tags=['mart', 'gold', 'customer']
  )
}}

WITH customer_purchases AS (
  SELECT
    c.CustomerSK,
    COUNT(DISTINCT fs.OrderID) AS TotalPurchases,
    SUM(fs.finalprice) AS TotalSpend,
    AVG(fs.finalprice) AS AvgOrderValue,
    MIN(d.Date) AS FirstPurchaseDate,
    MAX(d.Date) AS LastPurchaseDate,
    DATEDIFF(CURRENT_DATE(), MAX(d.Date)) AS DaysSinceLastPurchase
  FROM {{ ref('fact_sales') }} fs
  INNER JOIN {{ ref('dim_customer') }} c ON fs.CustomerSK = c.CustomerSK
  INNER JOIN {{ ref('dim_date') }} d ON fs.OrderDateID = d.DateID
  GROUP BY c.CustomerSK
)

SELECT
  c.CustomerSK AS CustomerKey,
  c.CustomerID,
  c.CustomerName,
  c.CustomerMail AS Email,
  c.CustomerContact AS Phone,
  NULL AS City,
  NULL AS State,
  COALESCE(cp.TotalPurchases, 0) AS TotalPurchases,
  ROUND(COALESCE(cp.TotalSpend, 0), 2) AS TotalSpend,
  ROUND(COALESCE(cp.AvgOrderValue, 0), 2) AS AvgOrderValue,
  cp.FirstPurchaseDate,
  cp.LastPurchaseDate,
  cp.DaysSinceLastPurchase,
  CASE
    WHEN COALESCE(cp.TotalPurchases, 0) = 0 THEN 'New Customer'
    WHEN cp.TotalPurchases = 1 THEN 'New Customer'
    WHEN cp.TotalPurchases BETWEEN 2 AND 5 THEN 'Returning Customer'
    WHEN cp.TotalPurchases > 5 THEN 'VIP Customer'
  END AS CustomerSegment,
  CASE
    WHEN cp.DaysSinceLastPurchase IS NULL THEN 'Inactive'
    WHEN cp.DaysSinceLastPurchase <= 30 THEN 'Active'
    WHEN cp.DaysSinceLastPurchase <= 90 THEN 'At Risk'
    ELSE 'Churned'
  END AS ActivityStatus
FROM {{ ref('dim_customer') }} c
LEFT JOIN customer_purchases cp ON c.CustomerSK = cp.CustomerSK
WHERE c.IsCurrent = 1
