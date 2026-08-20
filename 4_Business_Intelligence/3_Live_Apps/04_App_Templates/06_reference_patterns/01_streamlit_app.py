# Databricks notebook source
# SkillAIPath Sales Dashboard - Streamlit App
# FREE EDITION COMPATIBLE
# PURPOSE: Production-grade Streamlit dashboard for real-time sales analytics
# DEPLOYMENT: Databricks Apps (serverless hosting)
# Updated: June 2026 - Latest Databricks Apps patterns

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Import Databricks connection (for Databricks Apps)
try:
    from databricks import sql
    from databricks.sdk.runtime import dbutils
except ImportError:
    st.warning("Running in local mode - using mock data")

# Page Configuration
st.set_page_config(
    page_title="SkillAIPath Sales Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration - Parameterized for plug-and-play
class DashboardConfig:
    CATALOG = os.getenv("SKILLAIPPATH_CATALOG", "sap_dev")
    SCHEMA_GOLD = os.getenv("SKILLAIPPATH_SCHEMA", "gold")

    # Table references
    TABLE_DAILY_SALES = f"{CATALOG}.{SCHEMA_GOLD}.daily_sales_summary"
    TABLE_PRODUCT_PERFORMANCE = f"{CATALOG}.{SCHEMA_GOLD}.product_performance"
    TABLE_CUSTOMER_SEGMENTS = f"{CATALOG}.{SCHEMA_GOLD}.customer_segments"

    # Refresh interval (seconds)
    REFRESH_INTERVAL = 300

    # Color scheme
    PRIMARY_COLOR = "#FF6B6B"
    SECONDARY_COLOR = "#4ECDC4"
    SUCCESS_COLOR = "#95E1D3"
    WARNING_COLOR = "#F38181"

# Custom CSS Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Database Connection Function
@st.cache_resource
def get_db_connection():
    """Create Databricks SQL connection (cached)"""
    try:
        connection = sql.connect(
            server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
            http_path=os.getenv("DATABRICKS_HTTP_PATH"),
            access_token=os.getenv("DATABRICKS_TOKEN")
        )
        return connection
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

# Data Loading Functions
@st.cache_data(ttl=DashboardConfig.REFRESH_INTERVAL)
def load_sales_data(days=30):
    """Load sales data for last N days"""
    try:
        conn = get_db_connection()
        if conn is None:
            return generate_mock_sales_data(days)

        query = f"""
        SELECT
            sale_date,
            total_revenue,
            total_orders,
            unique_customers,
            avg_order_value
        FROM {DashboardConfig.TABLE_DAILY_SALES}
        WHERE sale_date >= CURRENT_DATE() - INTERVAL {days} DAYS
        ORDER BY sale_date DESC
        """

        cursor = conn.cursor()
        cursor.execute(query)

        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()

        cursor.close()

        return pd.DataFrame(data, columns=columns)

    except Exception as e:
        st.warning(f"Using mock data due to error: {str(e)}")
        return generate_mock_sales_data(days)

@st.cache_data(ttl=DashboardConfig.REFRESH_INTERVAL)
def load_product_performance(top_n=10):
    """Load top N performing products"""
    try:
        conn = get_db_connection()
        if conn is None:
            return generate_mock_product_data(top_n)

        query = f"""
        SELECT
            product_name,
            total_revenue,
            total_quantity_sold,
            avg_rating
        FROM {DashboardConfig.TABLE_PRODUCT_PERFORMANCE}
        WHERE sale_month = DATE_TRUNC('MONTH', CURRENT_DATE())
        ORDER BY total_revenue DESC
        LIMIT {top_n}
        """

        cursor = conn.cursor()
        cursor.execute(query)

        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()

        cursor.close()

        return pd.DataFrame(data, columns=columns)

    except Exception as e:
        st.warning(f"Using mock data: {str(e)}")
        return generate_mock_product_data(top_n)

# Mock Data Generation (for testing/local development)
def generate_mock_sales_data(days=30):
    """Generate mock sales data for testing"""
    import numpy as np

    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    data = {
        'sale_date': dates,
        'total_revenue': np.random.uniform(50000, 150000, days),
        'total_orders': np.random.randint(100, 500, days),
        'unique_customers': np.random.randint(80, 400, days),
        'avg_order_value': np.random.uniform(400, 800, days)
    }

    return pd.DataFrame(data)

def generate_mock_product_data(top_n=10):
    """Generate mock product data for testing"""
    products = [f"Product {i}" for i in range(1, top_n + 1)]

    data = {
        'product_name': products,
        'total_revenue': [50000 - i*3000 for i in range(top_n)],
        'total_quantity_sold': [500 - i*30 for i in range(top_n)],
        'avg_rating': [4.5 - i*0.1 for i in range(top_n)]
    }

    return pd.DataFrame(data)

# Dashboard Header
st.markdown('<div class="main-header">SkillAIPath Sales Dashboard</div>', unsafe_allow_html=True)
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Sidebar Filters
st.sidebar.header("Filters")
days_to_show = st.sidebar.slider("Days to Display", 7, 90, 30)
top_products_count = st.sidebar.slider("Top Products", 5, 20, 10)

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Load Data
with st.spinner("Loading data..."):
    df_sales = load_sales_data(days=days_to_show)
    df_products = load_product_performance(top_n=top_products_count)

# KPI Metrics Row
st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_revenue = df_sales['total_revenue'].sum()
    st.metric(
        label="Total Revenue",
        value=f"₹{total_revenue:,.0f}",
        delta=f"{((df_sales['total_revenue'].iloc[0] / df_sales['total_revenue'].iloc[-1]) - 1) * 100:.1f}%" if len(df_sales) > 1 else "N/A"
    )

with col2:
    total_orders = df_sales['total_orders'].sum()
    st.metric(
        label="Total Orders",
        value=f"{total_orders:,.0f}",
        delta=f"{((df_sales['total_orders'].iloc[0] / df_sales['total_orders'].iloc[-1]) - 1) * 100:.1f}%" if len(df_sales) > 1 else "N/A"
    )

with col3:
    avg_order_value = df_sales['avg_order_value'].mean()
    st.metric(
        label="Avg Order Value",
        value=f"₹{avg_order_value:,.2f}"
    )

with col4:
    total_customers = df_sales['unique_customers'].sum()
    st.metric(
        label="Unique Customers",
        value=f"{total_customers:,.0f}"
    )

# Revenue Trend Chart
st.subheader("Revenue Trend")

fig_revenue = px.line(
    df_sales,
    x='sale_date',
    y='total_revenue',
    title=f"Daily Revenue - Last {days_to_show} Days",
    labels={'sale_date': 'Date', 'total_revenue': 'Revenue (₹)'},
    color_discrete_sequence=[DashboardConfig.PRIMARY_COLOR]
)

fig_revenue.update_layout(
    xaxis_title="Date",
    yaxis_title="Revenue (₹)",
    hovermode='x unified',
    height=400
)

st.plotly_chart(fig_revenue, use_container_width=True)

# Orders Trend Chart
st.subheader("Orders Trend")

fig_orders = px.bar(
    df_sales,
    x='sale_date',
    y='total_orders',
    title=f"Daily Orders - Last {days_to_show} Days",
    labels={'sale_date': 'Date', 'total_orders': 'Orders'},
    color_discrete_sequence=[DashboardConfig.SECONDARY_COLOR]
)

fig_orders.update_layout(
    xaxis_title="Date",
    yaxis_title="Orders",
    hovermode='x unified',
    height=400
)

st.plotly_chart(fig_orders, use_container_width=True)

# Product Performance Section
st.subheader("Top Performing Products")

col_product1, col_product2 = st.columns(2)

with col_product1:
    fig_product_revenue = px.bar(
        df_products,
        x='product_name',
        y='total_revenue',
        title="Revenue by Product",
        labels={'product_name': 'Product', 'total_revenue': 'Revenue (₹)'},
        color='total_revenue',
        color_continuous_scale='Viridis'
    )

    fig_product_revenue.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_product_revenue, use_container_width=True)

with col_product2:
    fig_product_quantity = px.bar(
        df_products,
        x='product_name',
        y='total_quantity_sold',
        title="Quantity Sold by Product",
        labels={'product_name': 'Product', 'total_quantity_sold': 'Quantity'},
        color='total_quantity_sold',
        color_continuous_scale='Cividis'
    )

    fig_product_quantity.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_product_quantity, use_container_width=True)

# Product Performance Table
st.subheader("Product Performance Details")
st.dataframe(
    df_products.style.format({
        'total_revenue': '₹{:,.2f}',
        'total_quantity_sold': '{:,.0f}',
        'avg_rating': '{:.2f}'
    }),
    use_container_width=True
)

# Footer
st.markdown("---")
st.markdown("""
**Data Sources:**
- Daily Sales Summary: sap_dev.gold.daily_sales_summary
- Product Performance: sap_dev.gold.product_performance
- Customer Segments: sap_dev.gold.customer_segments

**Deployment:**
- Platform: Databricks Apps (Serverless)
- Refresh Interval: 5 minutes (configurable)
- Authentication: Databricks OAuth

**Support:**
- For issues or feature requests, contact the Data Engineering team
""")

print("Dashboard rendering complete")