-- SkillAIPath Reorder Recommendations
SELECT
  warehouse_name,
  product_name,
  current_stock,
  reorder_point,
  recommended_qty,
  urgency,
  estimated_cost,
  days_until_stockout
FROM sap.inventory_management.fact_reorder_recommendations
ORDER BY urgency DESC, days_until_stockout ASC
