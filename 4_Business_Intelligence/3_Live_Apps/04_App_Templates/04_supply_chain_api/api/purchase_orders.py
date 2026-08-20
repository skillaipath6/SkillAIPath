"""Purchase Orders API routes"""
from flask import Blueprint, jsonify, request

purchase_orders_bp = Blueprint("purchase_orders", __name__, url_prefix="/api/v2/purchase-orders")

@purchase_orders_bp.route("/create", methods=["POST"])
def create_purchase_order():
    """Create new purchase order"""
    # Implementation in main app.py
    pass

@purchase_orders_bp.route("/list", methods=["GET"])
def list_purchase_orders():
    """List all purchase orders"""
    # Implementation in main app.py
    pass
