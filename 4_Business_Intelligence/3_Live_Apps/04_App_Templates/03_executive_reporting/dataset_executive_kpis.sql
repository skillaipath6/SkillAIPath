-- SkillAIPath Executive Dashboard
-- High-level business metrics for leadership

-- KPI: Overall Inventory Health
SELECT
  'Inventory Health' as metric_name,
  ROUND(SUM(inventory_value) / 10000000, 2) as value_cr,
  ROUND((SUM(inventory_value) - LAG(SUM(inventory_value)) OVER (ORDER BY DATE_TRUNC('month', updated_at))) 
         / LAG(SUM(inventory_value)) OVER (ORDER BY DATE_TRUNC('month', updated_at)) * 100, 1) as mom_change_pct,
  DATE_TRUNC('month', updated_at) as month
FROM sap.inventory_management.fact_inventory
GROUP BY DATE_TRUNC('month', updated_at)
ORDER BY month DESC
LIMIT 12

-- KPI: Turnover Ratio
SELECT
  warehouse_name,
  ROUND(SUM(units_sold) / AVG(current_stock), 2) as turnover_ratio,
  CASE 
    WHEN SUM(units_sold) / AVG(current_stock) > 8 THEN 'Excellent'
    WHEN SUM(units_sold) / AVG(current_stock) > 5 THEN 'Good'
    WHEN SUM(units_sold) / AVG(current_stock) > 3 THEN 'Fair'
    ELSE 'Poor'
  END as performance
FROM sap.inventory_management.fact_inventory
GROUP BY warehouse_name
ORDER BY turnover_ratio DESC

-- KPI: Cost of Stockouts (Lost Revenue)
SELECT
  DATE_TRUNC('month', stockout_date) as month,
  COUNT(DISTINCT product_id) as num_stockouts,
  ROUND(SUM(estimated_lost_revenue) / 100000, 2) as lost_revenue_lakhs,
  ROUND(AVG(stockout_duration_hours), 1) as avg_duration_hours
FROM sap.inventory_management.fact_stockout_events
GROUP BY DATE_TRUNC('month', stockout_date)
ORDER BY month DESC

-- KPI: Carrying Cost Efficiency
SELECT
  'Total Carrying Cost' as metric,
  ROUND(SUM(inventory_value * 0.25) / 10000000, 2) as annual_cost_cr,
  ROUND(AVG(days_on_hand), 0) as avg_days_on_hand,
  'Target: <45 days' as benchmark
FROM sap.inventory_management.fact_inventory
