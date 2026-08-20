-- SkillAIPath Inventory KPIs
SELECT
  COALESCE(SUM(inventory_value), 0) as total_inventory_value,
  COUNT(DISTINCT product_id) as total_products,
  SUM(CASE WHEN stock_status = 'Critical' THEN 1 ELSE 0 END) as critical_items,
  ROUND(AVG(CASE WHEN current_stock = 0 THEN 100.0 ELSE 0.0 END), 1) as pct_out_of_stock
FROM sap.inventory_management.fact_inventory
