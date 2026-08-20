"""Purchase Order data model"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class PurchaseOrderItem:
    """Individual item in a purchase order"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

@dataclass
class PurchaseOrder:
    """Represents a purchase order"""
    po_number: str
    supplier_id: str
    supplier_name: Optional[str]
    items: List[PurchaseOrderItem]
    status: str  # pending_approval, approved, in_transit, received
    total_amount: float
    currency: str = "INR"
    created_at: datetime = None
    approved_at: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "po_number": self.po_number,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in self.items
            ],
            "status": self.status,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "expected_delivery": self.expected_delivery.isoformat() if self.expected_delivery else None
        }
