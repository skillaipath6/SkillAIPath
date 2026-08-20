-- Detailed Inventory Status
SELECT
  warehouse_name,
  product_name,
  current_stock,
  stock_status,
  inventory_value
FROM sap.inventory_management.fact_inventory
ORDER BY stock_status, inventory_value DESC
LIMIT 100
