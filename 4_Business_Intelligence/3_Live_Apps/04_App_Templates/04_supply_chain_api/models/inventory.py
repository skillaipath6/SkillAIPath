"""Inventory item data model"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class InventoryItem:
    """Represents an inventory item"""
    product_id: str
    product_name: str
    warehouse_id: str
    warehouse_name: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_point: int
    unit_price: float
    last_updated: datetime
    
    @property
    def needs_reorder(self) -> bool:
        """Check if item needs reordering"""
        return self.quantity_available < self.reorder_point
    
    @property
    def stock_status(self) -> str:
        """Get stock status"""
        if self.quantity_available == 0:
            return "OUT_OF_STOCK"
        elif self.quantity_available < self.reorder_point:
            return "LOW_STOCK"
        elif self.quantity_available < self.reorder_point * 2:
            return "ADEQUATE"
        else:
            return "EXCESS"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "quantity_on_hand": self.quantity_on_hand,
            "quantity_reserved": self.quantity_reserved,
            "quantity_available": self.quantity_available,
            "reorder_point": self.reorder_point,
            "unit_price": self.unit_price,
            "needs_reorder": self.needs_reorder,
            "stock_status": self.stock_status,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
