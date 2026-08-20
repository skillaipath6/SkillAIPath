"""Production-grade reorder logic and calculations for SkillAIPath Inventory System.

This module implements industry-standard inventory management algorithms:
- Reorder Point (ROP) calculation
- Safety Stock optimization
- Economic Order Quantity (EOQ)
- Demand forecasting

All functions include comprehensive validation, error handling, and logging.

Author: SkillAIPath Dev Team
Version: 2.0.0 (Production-Ready)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from config import config

logger = config.logger


@dataclass
class ReorderCalculation:
    """Result of reorder quantity calculation."""
    current_stock: int
    avg_daily_velocity: float
    lead_time_demand: int
    safety_stock: int
    reorder_point: int
    recommended_qty: int
    days_until_stockout: int
    urgency: str
    priority: int
    estimated_cost: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            'current_stock': self.current_stock,
            'daily_velocity': self.avg_daily_velocity,
            'days_until_stockout': self.days_until_stockout,
            'recommended_qty': self.recommended_qty,
            'urgency': self.urgency,
            'priority': self.priority,
            'estimated_cost': self.estimated_cost
        }


class InventoryCalculator:
    """Production-grade inventory calculations with validation."""
    
    # Default velocity when no sales history exists
    DEFAULT_VELOCITY = 10.0
    
    # Minimum days of sales history required for reliable calculations
    MIN_HISTORY_DAYS = 5
    
    def __init__(
        self,
        lead_time_days: Optional[int] = None,
        safety_stock_days: Optional[int] = None
    ):
        """Initialize calculator with business rules.
        
        Args:
            lead_time_days: Supplier lead time (defaults to config)
            safety_stock_days: Safety buffer days (defaults to config)
        """
        self.lead_time_days = lead_time_days or config.business_rules.lead_time_days
        self.safety_stock_days = safety_stock_days or config.business_rules.safety_stock_days
        
        logger.debug(f"InventoryCalculator initialized: lead_time={self.lead_time_days}d, safety_stock={self.safety_stock_days}d")
    
    def calculate_reorder_quantity(
        self,
        current_stock: int,
        avg_daily_velocity: float,
        unit_price: float
    ) -> ReorderCalculation:
        """Calculate recommended reorder quantity using Reorder Point method.
        
        Formula:
        - Lead Time Demand = Daily Velocity × Lead Time Days
        - Safety Stock = Daily Velocity × Safety Stock Days
        - Reorder Point = Lead Time Demand + Safety Stock
        - Reorder Quantity = max(0, Reorder Point - Current Stock)
        
        Args:
            current_stock: Current quantity on hand
            avg_daily_velocity: Average units sold per day
            unit_price: Unit price for cost estimation
            
        Returns:
            ReorderCalculation with all calculated fields
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if current_stock < 0:
            raise ValueError(f"Current stock cannot be negative: {current_stock}")
        if unit_price <= 0:
            raise ValueError(f"Unit price must be positive: {unit_price}")
        
        # Handle zero or missing velocity
        if pd.isna(avg_daily_velocity) or avg_daily_velocity < 0:
            logger.warning(f"Invalid velocity {avg_daily_velocity}, using default {self.DEFAULT_VELOCITY}")
            avg_daily_velocity = self.DEFAULT_VELOCITY
        
        # Calculate components
        lead_time_demand = avg_daily_velocity * self.lead_time_days
        safety_stock = avg_daily_velocity * self.safety_stock_days
        reorder_point = lead_time_demand + safety_stock
        
        # Calculate reorder quantity
        reorder_qty = max(0, int(np.ceil(reorder_point - current_stock)))
        
        # Calculate days until stockout
        if avg_daily_velocity > 0:
            days_until_stockout = max(0, int(np.floor(current_stock / avg_daily_velocity)))
        else:
            days_until_stockout = 999  # Unknown/infinite
        
        # Determine urgency level
        urgency, priority = self._calculate_urgency(current_stock, days_until_stockout)
        
        # Calculate estimated cost
        estimated_cost = reorder_qty * unit_price
        
        logger.debug(
            f"Reorder calc: stock={current_stock}, velocity={avg_daily_velocity:.2f}, "
            f"reorder_qty={reorder_qty}, urgency={urgency}"
        )
        
        return ReorderCalculation(
            current_stock=current_stock,
            avg_daily_velocity=round(avg_daily_velocity, 2),
            lead_time_demand=int(lead_time_demand),
            safety_stock=int(safety_stock),
            reorder_point=int(reorder_point),
            recommended_qty=reorder_qty,
            days_until_stockout=days_until_stockout,
            urgency=urgency,
            priority=priority,
            estimated_cost=round(estimated_cost, 2)
        )
    
    def _calculate_urgency(
        self,
        current_stock: int,
        days_until_stockout: int
    ) -> Tuple[str, int]:
        """Determine urgency level based on stock and days until stockout.
        
        Returns:
            Tuple of (urgency_label, priority_number)
        """
        if current_stock == 0:
            return "CRITICAL", 1
        elif days_until_stockout < self.lead_time_days:
            return "URGENT", 2
        elif days_until_stockout < (self.lead_time_days + self.safety_stock_days):
            return "MEDIUM", 3
        else:
            return "LOW", 4
    
    def calculate_economic_order_quantity(
        self,
        annual_demand: float,
        order_cost: float,
        holding_cost_percent: float,
        unit_price: float
    ) -> int:
        """Calculate Economic Order Quantity (EOQ).
        
        Formula: EOQ = sqrt((2 × Annual Demand × Order Cost) / (Holding Cost per Unit))
        Where Holding Cost per Unit = Unit Price × Holding Cost Percentage
        
        Args:
            annual_demand: Expected annual demand in units
            order_cost: Fixed cost per order (₹)
            holding_cost_percent: Annual holding cost as % of unit price (e.g., 0.25 for 25%)
            unit_price: Unit price (₹)
            
        Returns:
            Optimal order quantity
        """
        if any(x <= 0 for x in [annual_demand, order_cost, holding_cost_percent, unit_price]):
            logger.warning("Invalid EOQ inputs, returning 0")
            return 0
        
        holding_cost_per_unit = unit_price * holding_cost_percent
        eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)
        
        return int(np.ceil(eoq))


def generate_reorder_recommendations(
    inventory_df: pd.DataFrame,
    velocity_df: pd.DataFrame,
    lead_time_days: Optional[int] = None,
    safety_stock_days: Optional[int] = None
) -> pd.DataFrame:
    """Generate reorder recommendations for all low stock items.
    
    PRODUCTION FEATURES:
    - Validates input DataFrames
    - Handles missing velocity data
    - Filters to low stock items only
    - Sorts by urgency and stockout risk
    
    Args:
        inventory_df: Current inventory status
        velocity_df: Sales velocity data
        lead_time_days: Override default lead time
        safety_stock_days: Override default safety stock
        
    Returns:
        DataFrame with reorder recommendations sorted by urgency
    """
    # Validation
    if inventory_df.empty:
        logger.warning("Empty inventory DataFrame provided")
        return pd.DataFrame()
    
    if velocity_df.empty:
        logger.warning("Empty velocity DataFrame provided, using defaults")
    
    # Initialize calculator
    calculator = InventoryCalculator(lead_time_days, safety_stock_days)
    
    # Merge inventory with velocity
    merged = inventory_df.merge(
        velocity_df[['product_id', 'avg_daily_velocity']],
        on='product_id',
        how='left'
    )
    
    # Filter low stock items
    low_stock = merged[
        merged['quantity_on_hand'] < config.business_rules.low_stock_threshold
    ].copy()
    
    if low_stock.empty:
        logger.info("No low stock items found")
        return pd.DataFrame()
    
    logger.info(f"Processing {len(low_stock)} low stock items")
    
    # Calculate reorder for each item
    recommendations = []
    
    for _, row in low_stock.iterrows():
        try:
            calc = calculator.calculate_reorder_quantity(
                current_stock=row['quantity_on_hand'],
                avg_daily_velocity=row.get('avg_daily_velocity', calculator.DEFAULT_VELOCITY),
                unit_price=row['unit_price']
            )
            
            rec = {
                'warehouse_id': row.get('warehouse_id'),
                'warehouse_name': row.get('warehouse_name'),
                'product_id': row.get('product_id'),
                'product_name': row.get('product_name'),
                'category': row.get('category', 'Unknown'),
                **calc.to_dict(),
                'unit_price': row['unit_price']
            }
            recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Failed to calculate reorder for {row.get('product_name')}: {e}")
            continue
    
    if not recommendations:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(recommendations)
    
    # Sort by priority and stockout risk
    result_df = result_df.sort_values(['priority', 'days_until_stockout'])
    
    logger.info(
        f"Generated {len(result_df)} recommendations: "
        f"Critical={len(result_df[result_df['urgency']=='CRITICAL'])}, "
        f"Urgent={len(result_df[result_df['urgency']=='URGENT'])}"
    )
    
    return result_df


# ========================================
# UI Helper Functions
# ========================================

def format_currency(value: float) -> str:
    """Format value as Indian currency (₹).
    
    Args:
        value: Numeric value to format
        
    Returns:
        Formatted string with ₹ symbol
    """
    if pd.isna(value):
        return "₹0"
    return f"₹{value:,.0f}"


def get_urgency_color(urgency: str) -> str:
    """Get emoji indicator for urgency level.
    
    Args:
        urgency: Urgency level (CRITICAL, URGENT, MEDIUM, LOW)
        
    Returns:
        Emoji string
    """
    colors = {
        "CRITICAL": "🔴",
        "URGENT": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }
    return colors.get(urgency, "⚪")


def get_stock_status_color(status: str) -> str:
    """Get emoji indicator for stock status.
    
    Args:
        status: Stock status
        
    Returns:
        Emoji string
    """
    colors = {
        "OUT_OF_STOCK": "🔴",
        "LOW_STOCK": "🟠",
        "NORMAL": "🟢",
        "OVERSTOCKED": "🔵"
    }
    return colors.get(status, "⚪")


def calculate_reorder_summary(recommendations_df: pd.DataFrame) -> Dict[str, any]:
    """Calculate summary statistics for reorder recommendations.
    
    Args:
        recommendations_df: DataFrame with reorder recommendations
        
    Returns:
        Dictionary with summary metrics
    """
    if recommendations_df.empty:
        return {
            'total_items': 0,
            'critical_count': 0,
            'urgent_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'total_cost': 0,
            'total_quantity': 0
        }
    
    return {
        'total_items': len(recommendations_df),
        'critical_count': len(recommendations_df[recommendations_df['urgency'] == 'CRITICAL']),
        'urgent_count': len(recommendations_df[recommendations_df['urgency'] == 'URGENT']),
        'medium_count': len(recommendations_df[recommendations_df['urgency'] == 'MEDIUM']),
        'low_count': len(recommendations_df[recommendations_df['urgency'] == 'LOW']),
        'total_cost': recommendations_df['estimated_cost'].sum(),
        'total_quantity': recommendations_df['recommended_qty'].sum()
    }
