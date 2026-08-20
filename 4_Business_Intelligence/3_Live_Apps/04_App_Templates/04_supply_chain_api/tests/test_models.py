"""Data model tests"""
import pytest
from datetime import datetime
from models.inventory import InventoryItem
from models.purchase_order import PurchaseOrder, PurchaseOrderItem

def test_inventory_item_needs_reorder():
    """Test inventory item reorder logic"""
    item = InventoryItem(
        product_id="P001",
        product_name="Product A",
        warehouse_id="WH001",
        warehouse_name="Mumbai",
        quantity_on_hand=50,
        quantity_reserved=10,
        quantity_available=40,
        reorder_point=100,
        unit_price=1500.00,
        last_updated=datetime.now()
    )
    
    assert item.needs_reorder == True
    assert item.stock_status == "LOW_STOCK"

def test_inventory_item_adequate_stock():
    """Test inventory item with adequate stock"""
    item = InventoryItem(
        product_id="P001",
        product_name="Product A",
        warehouse_id="WH001",
        warehouse_name="Mumbai",
        quantity_on_hand=250,
        quantity_reserved=10,
        quantity_available=240,
        reorder_point=100,
        unit_price=1500.00,
        last_updated=datetime.now()
    )
    
    assert item.needs_reorder == False
    assert item.stock_status == "EXCESS"

def test_purchase_order_total():
    """Test purchase order total calculation"""
    items = [
        PurchaseOrderItem("P001", "Product A", 10, 50.00),
        PurchaseOrderItem("P002", "Product B", 5, 100.00)
    ]
    
    po = PurchaseOrder(
        po_number="PO-001",
        supplier_id="SUP001",
        supplier_name="Supplier A",
        items=items,
        status="pending_approval",
        total_amount=1000.00,
        created_at=datetime.now()
    )
    
    # Calculate expected total from items
    expected_total = sum(item.total_price for item in items)
    assert expected_total == 1000.00
