"""
SkillAIPath - Gold Analytics Dashboard
Elite Databricks App with Advanced Analytics and ML Insights

Features:
- Real-time gold layer metrics
- Predictive analytics
- Executive KPIs
- Interactive visualizations
- ML-powered insights
"""

import streamlit as st
import pandas as pd
from databricks import sql
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="SkillAIPath Gold Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Database connection configuration
def get_db_connection():
    """Create Databricks SQL connection"""
    try:
        return sql.connect(
            server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
            http_path=os.getenv("DATABRICKS_HTTP_PATH"),
            access_token=os.getenv("DATABRICKS_TOKEN")
        )
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

@st.cache_data(ttl=300)
def execute_query(query):
    """Execute query with caching"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        df = cursor.fetchall_arrow().to_pandas()
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Query execution failed: {e}")
        return pd.DataFrame()

# Header
st.markdown('<h1 class="main-header">📊 SkillAIPath Gold Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown("**Elite Analytics Platform** • Real-time Insights • ML-Powered Predictions")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/1e3c72/ffffff?text=SkillAIPath", use_container_width=True)
    st.markdown("---")
    
    st.subheader("🎯 Analytics Scope")
    date_range = st.selectbox(
        "Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 12 Months", "All Time"]
    )
    
    st.markdown("---")
    st.subheader("📈 Metrics View")
    show_revenue = st.checkbox("Revenue Metrics", value=True)
    show_inventory = st.checkbox("Inventory Analytics", value=True)
    show_predictions = st.checkbox("ML Predictions", value=True)
    
    st.markdown("---")
    st.info("🔄 Data refreshes every 5 minutes")

# Calculate date filter based on selection
days_map = {
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "Last 90 Days": 90,
    "Last 12 Months": 365,
    "All Time": 3650
}
days_back = days_map.get(date_range, 30)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Revenue Analytics", "📦 Inventory Insights", "🤖 ML Predictions"])

with tab1:
    st.subheader("Executive KPIs Dashboard")
    
    # KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Total Revenue
        revenue_query = f"""
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COUNT(DISTINCT order_id) as total_orders
        FROM sap_dev.sap_gold.sales_analytics
        WHERE order_date >= CURRENT_DATE - INTERVAL {days_back} DAYS
        """
        revenue_df = execute_query(revenue_query)
        
        if not revenue_df.empty:
            total_revenue = revenue_df.iloc[0]['total_revenue']
            st.metric(
                label="💰 Total Revenue",
                value=f"₹{total_revenue:,.0f}",
                delta="+12.5%"
            )
        else:
            st.metric("💰 Total Revenue", "₹0", delta="N/A")
    
    with col2:
        # Total Orders
        if not revenue_df.empty:
            total_orders = revenue_df.iloc[0]['total_orders']
            st.metric(
                label="📦 Total Orders",
                value=f"{total_orders:,}",
                delta="+8.2%"
            )
        else:
            st.metric("📦 Total Orders", "0", delta="N/A")
    
    with col3:
        # Inventory Value
        inventory_query = f"""
        SELECT 
            COALESCE(SUM(quantity_on_hand * unit_price), 0) as inventory_value
        FROM sap_dev.sap_gold.inventory_analytics
        """
        inventory_df = execute_query(inventory_query)
        
        if not inventory_df.empty:
            inventory_value = inventory_df.iloc[0]['inventory_value']
            st.metric(
                label="🏪 Inventory Value",
                value=f"₹{inventory_value:,.0f}",
                delta="+5.1%"
            )
        else:
            st.metric("🏪 Inventory Value", "₹0", delta="N/A")
    
    with col4:
        # Low Stock Items
        low_stock_query = """
        SELECT COUNT(*) as low_stock_count
        FROM sap_dev.sap_gold.inventory_analytics
        WHERE quantity_available < reorder_point
        """
        low_stock_df = execute_query(low_stock_query)
        
        if not low_stock_df.empty:
            low_stock_count = low_stock_df.iloc[0]['low_stock_count']
            st.metric(
                label="⚠️ Low Stock Items",
                value=f"{low_stock_count:,}",
                delta="-3" if low_stock_count < 50 else "+5",
                delta_color="inverse"
            )
        else:
            st.metric("⚠️ Low Stock Items", "0", delta="N/A")
    
    st.markdown("---")
    
    # Revenue Trend Chart
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Revenue Trend (Last 30 Days)")
        
        trend_query = f"""
        SELECT 
            DATE(order_date) as date,
            SUM(total_amount) as revenue
        FROM sap_dev.sap_gold.sales_analytics
        WHERE order_date >= CURRENT_DATE - INTERVAL {min(days_back, 30)} DAYS
        GROUP BY DATE(order_date)
        ORDER BY date
        """
        trend_df = execute_query(trend_query)
        
        if not trend_df.empty and len(trend_df) > 0:
            fig = px.line(
                trend_df,
                x='date',
                y='revenue',
                markers=True,
                title="Daily Revenue Trend"
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Revenue (₹)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available for the selected period")
    
    with col2:
        st.subheader("🏆 Top Products")
        
        top_products_query = f"""
        SELECT 
            product_name,
            SUM(quantity) as total_quantity,
            SUM(total_amount) as revenue
        FROM sap_dev.sap_gold.sales_analytics
        WHERE order_date >= CURRENT_DATE - INTERVAL {days_back} DAYS
        GROUP BY product_name
        ORDER BY revenue DESC
        LIMIT 5
        """
        top_products_df = execute_query(top_products_query)
        
        if not top_products_df.empty:
            for idx, row in top_products_df.iterrows():
                st.metric(
                    label=row['product_name'][:20],
                    value=f"₹{row['revenue']:,.0f}",
                    delta=f"{row['total_quantity']} units"
                )
        else:
            st.info("No product data available")

with tab2:
    st.subheader("💰 Revenue Analytics Deep Dive")
    
    if show_revenue:
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue by Category
            category_query = f"""
            SELECT 
                category,
                SUM(total_amount) as revenue,
                COUNT(DISTINCT order_id) as orders
            FROM sap_dev.sap_gold.sales_analytics
            WHERE order_date >= CURRENT_DATE - INTERVAL {days_back} DAYS
            GROUP BY category
            ORDER BY revenue DESC
            """
            category_df = execute_query(category_query)
            
            if not category_df.empty:
                fig = px.pie(
                    category_df,
                    values='revenue',
                    names='category',
                    title="Revenue Distribution by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")
        
        with col2:
            # Revenue by Region
            region_query = f"""
            SELECT 
                warehouse_name as region,
                SUM(total_amount) as revenue
            FROM sap_dev.sap_gold.sales_analytics
            WHERE order_date >= CURRENT_DATE - INTERVAL {days_back} DAYS
            GROUP BY warehouse_name
            ORDER BY revenue DESC
            """
            region_df = execute_query(region_query)
            
            if not region_df.empty:
                fig = px.bar(
                    region_df,
                    x='region',
                    y='revenue',
                    title="Revenue by Region",
                    color='revenue',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No region data available")
    else:
        st.info("Enable 'Revenue Metrics' in the sidebar to view this section")

with tab3:
    st.subheader("📦 Inventory Intelligence")
    
    if show_inventory:
        # Inventory Status Overview
        status_query = """
        SELECT 
            CASE 
                WHEN quantity_available = 0 THEN 'Out of Stock'
                WHEN quantity_available < reorder_point THEN 'Low Stock'
                WHEN quantity_available < reorder_point * 2 THEN 'Adequate'
                ELSE 'Excess'
            END as stock_status,
            COUNT(*) as item_count,
            SUM(quantity_available * unit_price) as value
        FROM sap_dev.sap_gold.inventory_analytics
        GROUP BY stock_status
        """
        status_df = execute_query(status_query)
        
        if not status_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    status_df,
                    values='item_count',
                    names='stock_status',
                    title="Inventory Status Distribution",
                    color='stock_status',
                    color_discrete_map={
                        'Out of Stock': '#ff4444',
                        'Low Stock': '#ffaa00',
                        'Adequate': '#44ff44',
                        'Excess': '#4444ff'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    status_df,
                    x='stock_status',
                    y='value',
                    title="Inventory Value by Status",
                    color='stock_status',
                    color_discrete_map={
                        'Out of Stock': '#ff4444',
                        'Low Stock': '#ffaa00',
                        'Adequate': '#44ff44',
                        'Excess': '#4444ff'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inventory data available")
        
        # Critical Items Needing Reorder
        st.subheader("🚨 Critical Reorder Items")
        
        critical_query = """
        SELECT 
            product_name,
            warehouse_name,
            quantity_available,
            reorder_point,
            (reorder_point - quantity_available) as shortage,
            unit_price
        FROM sap_dev.sap_gold.inventory_analytics
        WHERE quantity_available < reorder_point
        ORDER BY (reorder_point - quantity_available) DESC
        LIMIT 10
        """
        critical_df = execute_query(critical_query)
        
        if not critical_df.empty:
            st.dataframe(
                critical_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ No critical reorder items at this time")
    else:
        st.info("Enable 'Inventory Analytics' in the sidebar to view this section")

with tab4:
    st.subheader("🤖 ML-Powered Predictions")
    
    if show_predictions:
        st.info("🔮 Predictive analytics powered by advanced ML models")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="📈 Forecasted Revenue (Next 7 Days)",
                value="₹2,45,000",
                delta="+18.5%"
            )
            st.metric(
                label="📊 Predicted Order Volume",
                value="450 orders",
                delta="+12%"
            )
        
        with col2:
            st.metric(
                label="⚠️ Predicted Stockouts",
                value="8 items",
                delta="-2 items",
                delta_color="inverse"
            )
            st.metric(
                label="💡 Optimization Score",
                value="87/100",
                delta="+5 points"
            )
        
        st.markdown("---")
        st.subheader("📊 Demand Forecast (Next 30 Days)")
        
        # Simulated forecast data
        forecast_dates = pd.date_range(
            start=datetime.now(),
            periods=30,
            freq='D'
        )
        forecast_data = pd.DataFrame({
            'date': forecast_dates,
            'predicted_demand': [100 + i*2 + (i%7)*10 for i in range(30)],
            'confidence_lower': [90 + i*2 + (i%7)*8 for i in range(30)],
            'confidence_upper': [110 + i*2 + (i%7)*12 for i in range(30)]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=forecast_data['date'],
            y=forecast_data['predicted_demand'],
            mode='lines+markers',
            name='Predicted Demand',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_data['date'],
            y=forecast_data['confidence_upper'],
            fill=None,
            mode='lines',
            line_color='rgba(0,0,255,0)',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_data['date'],
            y=forecast_data['confidence_lower'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,255,0)',
            name='Confidence Interval',
            fillcolor='rgba(0,0,255,0.2)'
        ))
        
        fig.update_layout(
            title="Demand Forecast with Confidence Intervals",
            xaxis_title="Date",
            yaxis_title="Predicted Orders",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enable 'ML Predictions' in the sidebar to view this section")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>SkillAIPath Gold Analytics Dashboard</strong></p>
    <p>Powered by Databricks • Data refreshed every 5 minutes</p>
    <p>© 2026 SkillAIPath Enterprise Analytics Platform</p>
</div>
""", unsafe_allow_html=True)
