"""Webhook data model"""
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Webhook:
    """Represents a webhook registration"""
    webhook_id: str
    callback_url: str
    events: List[str]  # e.g., ["inventory.low_stock", "po.created"]
    status: str  # active, paused, failed
    created_at: datetime
    last_triggered: datetime = None
    failure_count: int = 0
    
    @property
    def is_healthy(self) -> bool:
        """Check if webhook is healthy"""
        return self.status == "active" and self.failure_count < 3
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "webhook_id": self.webhook_id,
            "callback_url": self.callback_url,
            "events": self.events,
            "status": self.status,
            "is_healthy": self.is_healthy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "failure_count": self.failure_count
        }
