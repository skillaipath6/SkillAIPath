"""🏭 Inventory Command Center - Production Application

Real-time inventory monitoring with reorder approval workflow.
Production-grade with error handling, logging, caching, and proper architecture.

DATA SOURCES:
- Unity Catalog: sap_dev.gold.mart_inventory_health (analytics)
- Lakebase Postgres: reorder_approvals (operational transactions)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import sys
import os

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../_shared'))

from config import config
from db_manager import get_database_manager
from logger import setup_logging
from error_handlers import handle_errors, ValidationError, show_error_with_recovery
from validators import Validator

# Page configuration
st.set_page_config(
    page_title="Inventory Command Center",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
logger = setup_logging("InventoryCommandCenter", config.app.log_level)


class InventoryItem:
    """Represents a single inventory item with health metrics."""
    
    def __init__(self, row: Dict):
        self.product_sk: int = row.get('product_sk', 0)
        self.product_name: str = row.get('ProductName', 'Unknown')
        self.warehouse_sk: int = row.get('warehouse_sk', 0)
        self.warehouse_name: str = row.get('WarehouseName', 'Unknown')
        self.current_stock: int = row.get('CurrentStock', 0)
        self.recommended_qty: int = row.get('RecommendedQty', 0)
        self.health_status: str = row.get('HealthStatus', 'Unknown')
        self.days_of_stock: float = row.get('DaysOfStock', 0.0)
    
    @property
    def urgency(self) -> str:
        """Calculate urgency level."""
        if self.health_status == 'Critical':
            return 'Critical'
        elif self.days_of_stock < 3:
            return 'High'
        elif self.days_of_stock < 7:
            return 'Medium'
        return 'Low'
    
    @property
    def stock_gap(self) -> int:
        """Calculate stock gap (needed - current)."""
        return max(0, self.recommended_qty - self.current_stock)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame."""
        return {
            'product_sk': self.product_sk,
            'product_name': self.product_name,
            'warehouse_sk': self.warehouse_sk,
            'warehouse_name': self.warehouse_name,
            'current_stock': self.current_stock,
            'recommended_qty': self.recommended_qty,
            'stock_gap': self.stock_gap,
            'health_status': self.health_status,
            'urgency': self.urgency,
            'days_of_stock': self.days_of_stock
        }


class InventoryDataService:
    """Service for fetching inventory data from Unity Catalog."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_critical_inventory(_self, health_filter: List[str] = None) -> List[InventoryItem]:
        """Fetch critical inventory items with caching."""
        logger.info("Fetching critical inventory data")
        
        try:
            health_filter = health_filter or ['Critical', 'Understock']
            filter_str = "', '".join(health_filter)
            
            query = f"""
                SELECT 
                    ProductSK as product_sk,
                    ProductName,
                    WarehouseSK as warehouse_sk,
                    WarehouseName,
                    CurrentStock,
                    CAST(CurrentStock * 1.5 AS INT) as RecommendedQty,
                    HealthStatus,
                    DaysOfStock
                FROM {config.unity_catalog.catalog}.gold.mart_inventory_health
                WHERE HealthStatus IN ('{filter_str}')
                AND CurrentStock < 100
                ORDER BY 
                    CASE HealthStatus 
                        WHEN 'Critical' THEN 1 
                        WHEN 'Understock' THEN 2 
                        ELSE 3 
                    END,
                    CurrentStock ASC
                LIMIT 50
            """
            
            with _self.db_manager.unity_catalog_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
            items = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                items.append(InventoryItem(row_dict))
            
            logger.info(f"Fetched {len(items)} critical inventory items")
            return items
            
        except Exception as e:
            logger.error(f"Failed to fetch inventory data: {e}")
            st.error(f"❌ Failed to load inventory data: {str(e)}")
            return []
    
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def get_inventory_summary(_self) -> Dict[str, int]:
        """Get inventory health summary counts."""
        try:
            query = f"""
                SELECT 
                    HealthStatus,
                    COUNT(*) as count
                FROM {config.unity_catalog.catalog}.gold.mart_inventory_health
                WHERE CurrentStock < 100
                GROUP BY HealthStatus
            """
            
            with _self.db_manager.unity_catalog_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            summary = {
                'Critical': 0,
                'Understock': 0,
                'Healthy': 0
            }
            
            for row in rows:
                status, count = row
                if status in summary:
                    summary[status] = count
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to fetch inventory summary: {e}")
            return {'Critical': 0, 'Understock': 0, 'Healthy': 0}


class ReorderApprovalService:
    """Service for managing reorder approvals in Lakebase."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    @handle_errors("Failed to create reorder request")
    def create_reorder_request(
        self, 
        item: InventoryItem,
        requested_qty: int,
        notes: str = ""
    ) -> bool:
        """Create a new reorder approval request."""
        
        # Validate quantity
        validation = Validator.validate_quantity(requested_qty, min_value=1, max_value=10000)
        if not validation:
            raise ValidationError(validation.message)
        
        try:
            with self.db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reorder_approvals (
                        product_sk, product_name, warehouse_sk, warehouse_name,
                        recommended_qty, current_stock, urgency, status,
                        notes, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item.product_sk,
                    item.product_name,
                    item.warehouse_sk,
                    item.warehouse_name,
                    requested_qty,
                    item.current_stock,
                    item.urgency,
                    'pending',
                    notes,
                    datetime.now()
                ))
            
            logger.info(f"Created reorder request for {item.product_name} at {item.warehouse_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create reorder request: {e}")
            raise
    
    @handle_errors("Failed to approve request")
    def approve_request(self, approval_id: int, approved_by: str) -> bool:
        """Approve a reorder request."""
        try:
            with self.db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    UPDATE reorder_approvals 
                    SET status = 'approved',
                        approved_by = %s,
                        updated_at = %s
                    WHERE approval_id = %s
                """, (approved_by, datetime.now(), approval_id))
            
            logger.info(f"Approved reorder request {approval_id} by {approved_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve request: {e}")
            raise
    
    @handle_errors("Failed to reject request")
    def reject_request(self, approval_id: int, reason: str) -> bool:
        """Reject a reorder request."""
        try:
            with self.db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    UPDATE reorder_approvals 
                    SET status = 'rejected',
                        rejected_reason = %s,
                        updated_at = %s
                    WHERE approval_id = %s
                """, (reason, datetime.now(), approval_id))
            
            logger.info(f"Rejected reorder request {approval_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject request: {e}")
            raise
    
    @st.cache_data(ttl=30)  # Cache for 30 seconds
    def get_pending_approvals(_self) -> pd.DataFrame:
        """Get all pending approval requests."""
        try:
            with _self.db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        approval_id, product_name, warehouse_name,
                        recommended_qty, current_stock, urgency,
                        notes, created_at
                    FROM reorder_approvals
                    WHERE status = 'pending'
                    ORDER BY 
                        CASE urgency 
                            WHEN 'Critical' THEN 1 
                            WHEN 'High' THEN 2 
                            WHEN 'Medium' THEN 3 
                            ELSE 4 
                        END,
                        created_at DESC
                """)
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            
            if rows:
                return pd.DataFrame(rows, columns=columns)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to fetch pending approvals: {e}")
            return pd.DataFrame()


def render_header():
    """Render application header."""
    st.title("🏭 Inventory Command Center")
    st.markdown("**Real-Time Monitoring | Approval Workflow | Production System**")
    st.markdown("---")


def render_metrics(summary: Dict[str, int]):
    """Render key metrics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚨 Critical Items",
            value=summary['Critical'],
            delta=None,
            help="Items with less than 3 days of stock"
        )
    
    with col2:
        st.metric(
            label="⚠️ Understock Items",
            value=summary['Understock'],
            delta=None,
            help="Items below optimal stock levels"
        )
    
    with col3:
        st.metric(
            label="✅ Healthy Items",
            value=summary['Healthy'],
            delta=None,
            help="Items at healthy stock levels"
        )
    
    with col4:
        total = sum(summary.values())
        critical_pct = (summary['Critical'] / total * 100) if total > 0 else 0
        st.metric(
            label="📊 Critical %",
            value=f"{critical_pct:.1f}%",
            delta=None,
            help="Percentage of critical items"
        )


def render_inventory_table(items: List[InventoryItem]):
    """Render inventory items table."""
    if not items:
        st.info("ℹ️ No critical inventory items found")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame([item.to_dict() for item in items])
    
    # Color code by urgency
    def highlight_urgency(row):
        if row['urgency'] == 'Critical':
            return ['background-color: #ffebee'] * len(row)
        elif row['urgency'] == 'High':
            return ['background-color: #fff3e0'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        df[['product_name', 'warehouse_name', 'current_stock', 'recommended_qty', 'stock_gap', 'urgency']],
        use_container_width=True,
        hide_index=True
    )


def render_reorder_form(items: List[InventoryItem], approval_service: ReorderApprovalService):
    """Render reorder request form."""
    st.subheader("📝 Create Reorder Request")
    
    if not items:
        st.warning("No items available for reorder")
        return
    
    with st.form("reorder_form"):
        # Item selection
        item_options = [f"{item.product_name} @ {item.warehouse_name}" for item in items]
        selected_idx = st.selectbox("Select Item", range(len(item_options)), format_func=lambda x: item_options[x])
        selected_item = items[selected_idx]
        
        # Show current status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Stock", selected_item.current_stock)
        with col2:
            st.metric("Recommended", selected_item.recommended_qty)
        with col3:
            st.metric("Stock Gap", selected_item.stock_gap)
        
        # Quantity input
        requested_qty = st.number_input(
            "Quantity to Order",
            min_value=1,
            max_value=10000,
            value=selected_item.stock_gap,
            help="Enter the quantity you want to order"
        )
        
        # Notes
        notes = st.text_area("Notes (optional)", max_length=500)
        
        # Submit
        submitted = st.form_submit_button("🚀 Submit Request", type="primary")
        
        if submitted:
            with st.spinner("Creating reorder request..."):
                success = approval_service.create_reorder_request(
                    selected_item,
                    requested_qty,
                    notes
                )
                
                if success:
                    st.success(f"✅ Reorder request created for {selected_item.product_name}!")
                    st.cache_data.clear()  # Clear cache to refresh data
                    st.rerun()


def render_pending_approvals(approval_service: ReorderApprovalService):
    """Render pending approvals section."""
    st.subheader("⏳ Pending Approvals")
    
    df = approval_service.get_pending_approvals()
    
    if df.empty:
        st.info("✓ No pending approvals")
        return
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Approval actions
    st.markdown("**Actions:**")
    col1, col2 = st.columns(2)
    
    with col1:
        approval_id = st.number_input("Approval ID", min_value=1, step=1)
        if st.button("✅ Approve", type="primary"):
            success = approval_service.approve_request(approval_id, "manager")
            if success:
                st.success("Approved!")
                st.cache_data.clear()
                st.rerun()
    
    with col2:
        reason = st.text_input("Rejection Reason")
        if st.button("❌ Reject"):
            if reason:
                success = approval_service.reject_request(approval_id, reason)
                if success:
                    st.success("Rejected!")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.error("Please provide a rejection reason")


def main():
    """Main application entry point."""
    try:
        # Initialize services
        db_manager = get_database_manager(config)
        inventory_service = InventoryDataService(db_manager)
        approval_service = ReorderApprovalService(db_manager)
        
        # Render UI
        render_header()
        
        # Sidebar filters
        with st.sidebar:
            st.header("⚙️ Filters")
            health_filter = st.multiselect(
                "Health Status",
                ['Critical', 'Understock', 'Healthy'],
                default=['Critical', 'Understock']
            )
            
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.rerun()
        
        # Get data
        with st.spinner("Loading inventory data..."):
            summary = inventory_service.get_inventory_summary()
            items = inventory_service.get_critical_inventory(health_filter)
        
        # Render metrics
        render_metrics(summary)
        
        st.markdown("---")
        
        # Render main content
        tab1, tab2, tab3 = st.tabs(["📋 Critical Inventory", "📝 Create Request", "⏳ Pending Approvals"])
        
        with tab1:
            render_inventory_table(items)
        
        with tab2:
            render_reorder_form(items, approval_service)
        
        with tab3:
            render_pending_approvals(approval_service)
        
        # Footer
        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Environment: {config.app.environment}")
        
    except Exception as e:
        logger.exception("Application error")
        st.error(f"❌ Application error: {str(e)}")
        
        if st.button("🔄 Retry"):
            st.rerun()


if __name__ == "__main__":
    main()
