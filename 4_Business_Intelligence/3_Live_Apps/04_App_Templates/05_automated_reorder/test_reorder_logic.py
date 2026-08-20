"""Unit tests for reorder_logic.py

Run with: pytest test_reorder_logic.py -v --cov=reorder_logic

Author: SkillAIPath Dev Team
Version: 2.0.0
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from reorder_logic import (
    InventoryCalculator,
    ReorderCalculation,
    generate_reorder_recommendations,
    format_currency,
    get_urgency_color,
    calculate_reorder_summary
)


class TestInventoryCalculator:
    """Test InventoryCalculator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = InventoryCalculator(lead_time_days=7, safety_stock_days=5)
    
    def test_normal_reorder_calculation(self):
        """Test reorder calculation with normal inputs."""
        result = self.calculator.calculate_reorder_quantity(
            current_stock=20,
            avg_daily_velocity=10.0,
            unit_price=100.0
        )
        
        assert isinstance(result, ReorderCalculation)
        assert result.current_stock == 20
        assert result.avg_daily_velocity == 10.0
        assert result.lead_time_demand == 70  # 10 * 7
        assert result.safety_stock == 50  # 10 * 5
        assert result.reorder_point == 120  # 70 + 50
        assert result.recommended_qty == 100  # max(0, 120 - 20)
        assert result.days_until_stockout == 2  # floor(20 / 10)
        assert result.urgency == "URGENT"
        assert result.priority == 2
        assert result.estimated_cost == 10000.0  # 100 * 100
    
    def test_zero_stock_critical(self):
        """Test that zero stock triggers CRITICAL urgency."""
        result = self.calculator.calculate_reorder_quantity(
            current_stock=0,
            avg_daily_velocity=5.0,
            unit_price=50.0
        )
        
        assert result.urgency == "CRITICAL"
        assert result.priority == 1
        assert result.days_until_stockout == 0
    
    def test_adequate_stock_low_priority(self):
        """Test that adequate stock results in LOW urgency."""
        result = self.calculator.calculate_reorder_quantity(
            current_stock=500,
            avg_daily_velocity=10.0,
            unit_price=100.0
        )
        
        assert result.urgency == "LOW"
        assert result.priority == 4
        assert result.recommended_qty == 0  # No reorder needed
    
    def test_zero_velocity_uses_default(self):
        """Test that zero velocity uses default value."""
        result = self.calculator.calculate_reorder_quantity(
            current_stock=10,
            avg_daily_velocity=0.0,
            unit_price=100.0
        )
        
        # Should use DEFAULT_VELOCITY (10.0)
        assert result.avg_daily_velocity == InventoryCalculator.DEFAULT_VELOCITY
        assert result.recommended_qty > 0
    
    def test_nan_velocity_uses_default(self):
        """Test that NaN velocity uses default value."""
        result = self.calculator.calculate_reorder_quantity(
            current_stock=10,
            avg_daily_velocity=np.nan,
            unit_price=100.0
        )
        
        assert result.avg_daily_velocity == InventoryCalculator.DEFAULT_VELOCITY
    
    def test_negative_stock_raises_error(self):
        """Test that negative stock raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            self.calculator.calculate_reorder_quantity(
                current_stock=-10,
                avg_daily_velocity=5.0,
                unit_price=100.0
            )
    
    def test_zero_price_raises_error(self):
        """Test that zero unit price raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            self.calculator.calculate_reorder_quantity(
                current_stock=10,
                avg_daily_velocity=5.0,
                unit_price=0.0
            )
    
    def test_negative_price_raises_error(self):
        """Test that negative unit price raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            self.calculator.calculate_reorder_quantity(
                current_stock=10,
                avg_daily_velocity=5.0,
                unit_price=-100.0
            )
    
    def test_eoq_calculation(self):
        """Test Economic Order Quantity calculation."""
        eoq = self.calculator.calculate_economic_order_quantity(
            annual_demand=10000,
            order_cost=50,
            holding_cost_percent=0.25,
            unit_price=100
        )
        
        # EOQ = sqrt((2 * 10000 * 50) / (100 * 0.25))
        # EOQ = sqrt(1000000 / 25) = sqrt(40000) = 200
        assert eoq == 200
    
    def test_eoq_invalid_inputs(self):
        """Test EOQ with invalid inputs returns 0."""
        assert self.calculator.calculate_economic_order_quantity(0, 50, 0.25, 100) == 0
        assert self.calculator.calculate_economic_order_quantity(10000, -50, 0.25, 100) == 0
        assert self.calculator.calculate_economic_order_quantity(10000, 50, -0.25, 100) == 0
        assert self.calculator.calculate_economic_order_quantity(10000, 50, 0.25, -100) == 0


class TestGenerateReorderRecommendations:
    """Test generate_reorder_recommendations function."""
    
    def test_empty_inventory_returns_empty(self):
        """Test that empty inventory DataFrame returns empty result."""
        inventory_df = pd.DataFrame()
        velocity_df = pd.DataFrame()
        
        result = generate_reorder_recommendations(inventory_df, velocity_df)
        
        assert result.empty
    
    def test_no_low_stock_returns_empty(self):
        """Test that no low stock items returns empty result."""
        inventory_df = pd.DataFrame({
            'product_id': [1, 2],
            'product_name': ['Product A', 'Product B'],
            'quantity_on_hand': [100, 200],  # All above threshold
            'unit_price': [50.0, 75.0],
            'warehouse_id': [1, 1],
            'warehouse_name': ['Warehouse 1', 'Warehouse 1'],
            'category': ['Category A', 'Category B']
        })
        
        velocity_df = pd.DataFrame({
            'product_id': [1, 2],
            'avg_daily_velocity': [5.0, 10.0]
        })
        
        result = generate_reorder_recommendations(inventory_df, velocity_df)
        
        assert result.empty
    
    def test_low_stock_generates_recommendations(self):
        """Test that low stock items generate recommendations."""
        inventory_df = pd.DataFrame({
            'product_id': [1, 2, 3],
            'product_name': ['Product A', 'Product B', 'Product C'],
            'quantity_on_hand': [10, 0, 30],  # All below threshold (50)
            'unit_price': [100.0, 200.0, 50.0],
            'warehouse_id': [1, 1, 2],
            'warehouse_name': ['WH1', 'WH1', 'WH2'],
            'category': ['Cat A', 'Cat B', 'Cat C']
        })
        
        velocity_df = pd.DataFrame({
            'product_id': [1, 2, 3],
            'avg_daily_velocity': [5.0, 10.0, 3.0]
        })
        
        result = generate_reorder_recommendations(inventory_df, velocity_df)
        
        assert not result.empty
        assert len(result) == 3
        assert 'recommended_qty' in result.columns
        assert 'urgency' in result.columns
        assert 'priority' in result.columns
        
        # Verify sorted by priority
        assert result.iloc[0]['priority'] <= result.iloc[-1]['priority']
        
        # Check zero stock is CRITICAL
        zero_stock = result[result['product_name'] == 'Product B'].iloc[0]
        assert zero_stock['urgency'] == 'CRITICAL'
        assert zero_stock['priority'] == 1


class TestHelperFunctions:
    """Test UI helper functions."""
    
    def test_format_currency_normal(self):
        """Test currency formatting with normal values."""
        assert format_currency(1000) == "₹1,000"
        assert format_currency(1234567.89) == "₹1,234,568"
        assert format_currency(0) == "₹0"
    
    def test_format_currency_nan(self):
        """Test currency formatting with NaN."""
        assert format_currency(np.nan) == "₹0"
        assert format_currency(None) == "₹0"
    
    def test_get_urgency_color(self):
        """Test urgency color mapping."""
        assert get_urgency_color("CRITICAL") == "🔴"
        assert get_urgency_color("URGENT") == "🟠"
        assert get_urgency_color("MEDIUM") == "🟡"
        assert get_urgency_color("LOW") == "🟢"
        assert get_urgency_color("UNKNOWN") == "⚪"
    
    def test_calculate_reorder_summary_empty(self):
        """Test summary calculation with empty DataFrame."""
        df = pd.DataFrame()
        summary = calculate_reorder_summary(df)
        
        assert summary['total_items'] == 0
        assert summary['critical_count'] == 0
        assert summary['total_cost'] == 0
    
    def test_calculate_reorder_summary_normal(self):
        """Test summary calculation with normal data."""
        df = pd.DataFrame({
            'urgency': ['CRITICAL', 'URGENT', 'URGENT', 'MEDIUM'],
            'estimated_cost': [1000, 2000, 1500, 500],
            'recommended_qty': [10, 20, 15, 5]
        })
        
        summary = calculate_reorder_summary(df)
        
        assert summary['total_items'] == 4
        assert summary['critical_count'] == 1
        assert summary['urgent_count'] == 2
        assert summary['medium_count'] == 1
        assert summary['total_cost'] == 5000
        assert summary['total_quantity'] == 50


class TestReorderCalculationDataclass:
    """Test ReorderCalculation dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        calc = ReorderCalculation(
            current_stock=10,
            avg_daily_velocity=5.0,
            lead_time_demand=35,
            safety_stock=25,
            reorder_point=60,
            recommended_qty=50,
            days_until_stockout=2,
            urgency="URGENT",
            priority=2,
            estimated_cost=5000.0
        )
        
        result = calc.to_dict()
        
        assert isinstance(result, dict)
        assert result['current_stock'] == 10
        assert result['daily_velocity'] == 5.0
        assert result['recommended_qty'] == 50
        assert result['urgency'] == "URGENT"


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=reorder_logic", "--cov-report=html"])
