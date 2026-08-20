"""Supply Chain API - Route modules"""
from .inventory import inventory_bp
from .purchase_orders import purchase_orders_bp
from .webhooks import webhooks_bp

__all__ = ["inventory_bp", "purchase_orders_bp", "webhooks_bp"]
