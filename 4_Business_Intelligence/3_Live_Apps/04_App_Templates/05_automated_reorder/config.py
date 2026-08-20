"""Production-grade configuration management for SkillAIPath Inventory Reorder System.

This module provides centralized configuration with:
- Environment variable support
- Type validation
- Default values
- Multi-environment support (dev/staging/prod)

Author: SkillAIPath Dev Team
Version: 2.0.0 (Production-Ready)
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database connection and table configuration."""
    catalog: str = field(default_factory=lambda: os.getenv("SKILLAIPPATH_CATALOG", "sap_dev"))
    schema_silver: str = field(default_factory=lambda: os.getenv("SKILLAIPPATH_SCHEMA_SILVER", "silver"))
    schema_bronze: str = field(default_factory=lambda: os.getenv("SKILLAIPPATH_SCHEMA_BRONZE", "bronze"))
    
    # SQL Warehouse connection (for Databricks Apps)
    server_hostname: Optional[str] = field(default_factory=lambda: os.getenv("DATABRICKS_SERVER_HOSTNAME"))
    http_path: Optional[str] = field(default_factory=lambda: os.getenv("DATABRICKS_HTTP_PATH"))
    access_token: Optional[str] = field(default_factory=lambda: os.getenv("DATABRICKS_TOKEN"))
    
    def get_table_path(self, schema: str, table: str) -> str:
        """Get fully qualified table name."""
        return f"{self.catalog}.{schema}.{table}"


@dataclass
class BusinessRulesConfig:
    """Business logic configuration for inventory reorder calculations."""
    lead_time_days: int = field(default_factory=lambda: int(os.getenv("LEAD_TIME_DAYS", "7")))
    safety_stock_days: int = field(default_factory=lambda: int(os.getenv("SAFETY_STOCK_DAYS", "5")))
    velocity_lookback_days: int = field(default_factory=lambda: int(os.getenv("VELOCITY_LOOKBACK_DAYS", "30")))
    low_stock_threshold: int = field(default_factory=lambda: int(os.getenv("LOW_STOCK_THRESHOLD", "50")))
    
    # Validation rules
    min_order_quantity: int = field(default_factory=lambda: int(os.getenv("MIN_ORDER_QUANTITY", "1")))
    max_order_quantity: int = field(default_factory=lambda: int(os.getenv("MAX_ORDER_QUANTITY", "10000")))
    max_unit_price: float = field(default_factory=lambda: float(os.getenv("MAX_UNIT_PRICE", "1000000.0")))
    
    def validate_order_quantity(self, quantity: int) -> tuple[bool, Optional[str]]:
        """Validate order quantity is within acceptable range."""
        if quantity < self.min_order_quantity:
            return False, f"Order quantity must be at least {self.min_order_quantity}"
        if quantity > self.max_order_quantity:
            return False, f"Order quantity cannot exceed {self.max_order_quantity}"
        return True, None
    
    def validate_unit_price(self, price: float) -> tuple[bool, Optional[str]]:
        """Validate unit price is reasonable."""
        if price <= 0:
            return False, "Unit price must be positive"
        if price > self.max_unit_price:
            return False, f"Unit price exceeds maximum allowed ({self.max_unit_price:,.0f})"
        return True, None


@dataclass
class AppConfig:
    """Main application configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    business_rules: BusinessRulesConfig = field(default_factory=BusinessRulesConfig)
    
    app_name: str = "SkillAIPath Inventory Reorder System"
    app_version: str = "2.0.0"
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    def __post_init__(self):
        """Initialize logging after config is created."""
        self._setup_logging()
        self.logger.info(f"{self.app_name} v{self.app_version} initialized")
    
    def _setup_logging(self):
        """Configure structured logging."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('SkillAIPath.InventoryReorder')


# Global configuration instance
config = AppConfig()
