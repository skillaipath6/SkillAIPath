"""SkillAIPath Inventory Reorder System - Main Application

Production-ready Streamlit application with:
- Security hardening (input validation, SQL injection prevention)
- Professional UI/UX with real-time updates
- Comprehensive error handling
- Structured logging and monitoring

Author: SkillAIPath Dev Team
Version: 2.0.0 (Production-Ready)
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Local imports
from config import config
from database import (
    get_inventory_status,
    calculate_sales_velocity,
    submit_purchase_order,
    get_recent_purchase_orders,
    get_warehouses,
    get_products
)
from reorder_logic import (
    generate_reorder_recommendations,
    format_currency,
    get_urgency_color,
    get_stock_status_color,
    calculate_reorder_summary
)

logger = config.logger

# ========================================
# PAGE CONFIGURATION
# ========================================

st.set_page_config(
    page_title="SkillAIPath Inventory Reorder",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .critical { color: #d32f2f; font-weight: 600; }
    .urgent { color: #f57c00; font-weight: 600; }
    .success { color: #388e3c; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ========================================
# HELPER FUNCTIONS
# ========================================

def display_header():
    """Display application header with branding."""
    st.markdown('<div class="main-header">📦 SkillAIPath Inventory Reorder System</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">Intelligent inventory management • Version {config.version} • '
        f'Environment: {config.environment}</div>',
        unsafe_allow_html=True
    )


def display_metrics(inventory_df: pd.DataFrame, recommendations_df: pd.DataFrame):
    """Display key metrics in dashboard cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_products = len(inventory_df['product_id'].unique()) if not inventory_df.empty else 0
        st.metric("Total Products", f"{total_products:,}")
    
    with col2:
        total_value = inventory_df['inventory_value'].sum() if not inventory_df.empty else 0
        st.metric("Total Inventory Value", format_currency(total_value))
    
    with col3:
        low_stock_count = len(inventory_df[inventory_df['quantity_on_hand'] < config.business_rules.low_stock_threshold])
        st.metric("Low Stock Items", f"{low_stock_count:,}", delta=None, delta_color="inverse")
    
    with col4:
        critical_count = len(recommendations_df[recommendations_df['urgency'] == 'CRITICAL']) if not recommendations_df.empty else 0
        st.metric("Critical Items", f"{critical_count:,}", delta=None, delta_color="inverse")


def format_dataframe_for_display(df: pd.DataFrame, column_config: dict = None) -> pd.DataFrame:
    """Format DataFrame for better display in Streamlit."""
    if df.empty:
        return df
    
    display_df = df.copy()
    
    # Format currency columns
    currency_cols = ['unit_price', 'estimated_cost', 'total_amount', 'inventory_value']
    for col in currency_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_currency)
    
    # Round numeric columns
    numeric_cols = ['daily_velocity']
    for col in numeric_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)
    
    return display_df


# ========================================
# MAIN APPLICATION
# ========================================

def main():
    """Main application entry point."""
    
    try:
        logger.info("Application started")
        
        # Display header
        display_header()
        
        # Sidebar configuration
        st.sidebar.header("⚙️ Configuration")
        st.sidebar.markdown(f"**Catalog:** `{config.database.catalog}`")
        st.sidebar.markdown(f"**Schema:** `{config.database.schema_silver}`")
        st.sidebar.markdown(f"**Lead Time:** {config.business_rules.lead_time_days} days")
        st.sidebar.markdown(f"**Safety Stock:** {config.business_rules.safety_stock_days} days")
        st.sidebar.markdown("---")
        
        # Page selection
        page = st.sidebar.radio(
            "📄 Navigate",
            ["Dashboard", "Reorder Recommendations", "Submit Purchase Order", "Recent Orders"]
        )
        
        # Load data (cached)
        with st.spinner("Loading inventory data..."):
            inventory_df = get_inventory_status()
            velocity_df = calculate_sales_velocity()
            
            if inventory_df.empty:
                st.error("⚠️ No inventory data found. Please check database connection and permissions.")
                logger.error("No inventory data loaded")
                return
        
        # Generate recommendations
        recommendations_df = generate_reorder_recommendations(inventory_df, velocity_df)
        
        # Route to selected page
        if page == "Dashboard":
            display_dashboard_page(inventory_df, recommendations_df)
        elif page == "Reorder Recommendations":
            display_recommendations_page(recommendations_df)
        elif page == "Submit Purchase Order":
            display_purchase_order_page()
        elif page == "Recent Orders":
            display_recent_orders_page()
        
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
            f"**Log Level:** {config.log_level}"
        )
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"⚠️ Application error: {str(e)}")
        st.info("Please contact support if the issue persists.")


# ========================================
# PAGE: DASHBOARD
# ========================================

def display_dashboard_page(inventory_df: pd.DataFrame, recommendations_df: pd.DataFrame):
    """Display main dashboard with KPIs and alerts."""
    
    st.header("📊 Dashboard")
    
    # Display metrics
    display_metrics(inventory_df, recommendations_df)
    
    st.markdown("---")
    
    # Urgent alerts
    if not recommendations_df.empty:
        critical_urgent = recommendations_df[recommendations_df['priority'] <= 2]
        
        if not critical_urgent.empty:
            st.subheader("🚨 Urgent Attention Required")
            
            for _, row in critical_urgent.head(10).iterrows():
                urgency_emoji = get_urgency_color(row['urgency'])
                with st.expander(f"{urgency_emoji} {row['product_name']} at {row['warehouse_name']} - {row['urgency']}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Stock", f"{row['current_stock']} units")
                    with col2:
                        st.metric("Days Until Stockout", f"{row['days_until_stockout']} days")
                    with col3:
                        st.metric("Recommended Order", f"{row['recommended_qty']} units")
                    
                    st.markdown(f"**Estimated Cost:** {format_currency(row['estimated_cost'])}")
    else:
        st.success("✅ No urgent reorder items. All inventory levels are adequate.")
    
    st.markdown("---")
    
    # Inventory by warehouse
    st.subheader("📍 Inventory by Warehouse")
    
    warehouse_summary = inventory_df.groupby('warehouse_name').agg({
        'product_id': 'count',
        'inventory_value': 'sum',
        'quantity_on_hand': 'sum'
    }).reset_index()
    
    warehouse_summary.columns = ['Warehouse', 'Products', 'Total Value', 'Total Units']
    warehouse_summary['Total Value'] = warehouse_summary['Total Value'].apply(format_currency)
    
    st.dataframe(warehouse_summary, use_container_width=True, hide_index=True)


# ========================================
# PAGE: REORDER RECOMMENDATIONS
# ========================================

def display_recommendations_page(recommendations_df: pd.DataFrame):
    """Display detailed reorder recommendations."""
    
    st.header("🔄 Reorder Recommendations")
    
    if recommendations_df.empty:
        st.success("✅ No items require reordering at this time.")
        return
    
    # Summary
    summary = calculate_reorder_summary(recommendations_df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", summary['total_items'])
    with col2:
        st.metric("🔴 Critical", summary['critical_count'])
    with col3:
        st.metric("🟠 Urgent", summary['urgent_count'])
    with col4:
        st.metric("Total Cost", format_currency(summary['total_cost']))
    
    st.markdown("---")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        urgency_filter = st.multiselect(
            "Filter by Urgency",
            options=['CRITICAL', 'URGENT', 'MEDIUM', 'LOW'],
            default=['CRITICAL', 'URGENT']
        )
    with col2:
        warehouse_filter = st.multiselect(
            "Filter by Warehouse",
            options=recommendations_df['warehouse_name'].unique(),
            default=recommendations_df['warehouse_name'].unique()
        )
    
    # Apply filters
    filtered_df = recommendations_df[
        (recommendations_df['urgency'].isin(urgency_filter)) &
        (recommendations_df['warehouse_name'].isin(warehouse_filter))
    ]
    
    if filtered_df.empty:
        st.info("No recommendations match the selected filters.")
        return
    
    # Display table
    st.subheader(f"📋 {len(filtered_df)} Recommendations")
    
    display_df = filtered_df[[
        'warehouse_name', 'product_name', 'current_stock', 'daily_velocity',
        'days_until_stockout', 'recommended_qty', 'urgency', 'unit_price', 'estimated_cost'
    ]].copy()
    
    # Add urgency emoji
    display_df.insert(0, '🚦', display_df['urgency'].apply(get_urgency_color))
    
    display_df = format_dataframe_for_display(display_df)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Download option
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Recommendations (CSV)",
        data=csv,
        file_name=f"sap_reorder_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


# ========================================
# PAGE: SUBMIT PURCHASE ORDER
# ========================================

def display_purchase_order_page():
    """Display purchase order submission form."""
    
    st.header("📝 Submit Purchase Order")
    
    # Load dropdowns
    warehouses_df = get_warehouses()
    products_df = get_products()
    
    if warehouses_df.empty or products_df.empty:
        st.error("Unable to load warehouse or product data.")
        return
    
    with st.form("purchase_order_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Warehouse selection
            warehouse_options = dict(zip(
                warehouses_df['warehouse_name'],
                warehouses_df['warehouse_id']
            ))
            selected_warehouse = st.selectbox(
                "Warehouse *",
                options=list(warehouse_options.keys())
            )
            warehouse_id = warehouse_options[selected_warehouse]
            
            # Quantity
            quantity = st.number_input(
                "Quantity *",
                min_value=config.business_rules.min_order_quantity,
                max_value=config.business_rules.max_order_quantity,
                value=100,
                step=10
            )
        
        with col2:
            # Product selection
            product_options = dict(zip(
                products_df['product_name'],
                products_df['product_id']
            ))
            selected_product = st.selectbox(
                "Product *",
                options=list(product_options.keys())
            )
            product_id = product_options[selected_product]
            
            # Unit price (prefilled from product)
            default_price = products_df[products_df['product_id'] == product_id]['unit_price'].iloc[0]
            unit_price = st.number_input(
                "Unit Price (₹) *",
                min_value=0.01,
                max_value=config.business_rules.max_unit_price,
                value=float(default_price),
                step=10.0,
                format="%.2f"
            )
        
        # Notes
        notes = st.text_area(
            "Notes (optional)",
            placeholder="Additional information about this order..."
        )
        
        # Summary
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Gross Amount", format_currency(quantity * unit_price))
        with col2:
            gst = (quantity * unit_price) * 0.18
            st.metric("GST (18%)", format_currency(gst))
        with col3:
            total = (quantity * unit_price) * 1.18
            st.metric("Total Amount", format_currency(total))
        
        # Submit button
        submitted = st.form_submit_button("✅ Submit Purchase Order", type="primary")
    
    if submitted:
        with st.spinner("Submitting purchase order..."):
            success, message = submit_purchase_order(
                warehouse_id=warehouse_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                notes=notes
            )
            
            if success:
                st.success(f"✅ {message}")
                logger.info(f"Purchase order submitted: {selected_product} x {quantity} to {selected_warehouse}")
            else:
                st.error(f"❌ {message}")
                logger.warning(f"Purchase order failed: {message}")


# ========================================
# PAGE: RECENT ORDERS
# ========================================

def display_recent_orders_page():
    """Display recently submitted purchase orders."""
    
    st.header("📜 Recent Purchase Orders")
    
    orders_df = get_recent_purchase_orders(limit=50)
    
    if orders_df.empty:
        st.info("No recent purchase orders found.")
        return
    
    st.markdown(f"Showing last **{len(orders_df)}** orders")
    
    display_df = format_dataframe_for_display(orders_df)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ========================================
# APPLICATION ENTRY POINT
# ========================================

if __name__ == "__main__":
    main()
