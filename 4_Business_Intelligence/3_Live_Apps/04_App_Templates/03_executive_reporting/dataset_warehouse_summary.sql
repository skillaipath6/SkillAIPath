-- Warehouse Summary for Bar Chart
SELECT
  warehouse_name,
  SUM(inventory_value) as total_inventory_value
FROM sap.inventory_management.fact_inventory
GROUP BY warehouse_name
ORDER BY total_inventory_value DESC
