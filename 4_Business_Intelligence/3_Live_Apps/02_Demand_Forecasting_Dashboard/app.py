"""📈 Demand Forecasting Dashboard - Production Application

ML-powered demand forecasting with model management, validation, and audit trail.
Production-grade with Prophet, error handling, caching, and performance metrics.

DATA SOURCES:
- Unity Catalog: sap_dev.silver.fact_sales (historical sales)
- Lakebase Postgres: forecast_runs (forecast history & audit)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from prophet import Prophet
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List
import sys
import os
import json

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../_shared'))

from config import config
from db_manager import get_database_manager
from logger import setup_logging
from error_handlers import handle_errors, ValidationError
from validators import Validator

# Page configuration
st.set_page_config(
    page_title="Demand Forecasting",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup logging
logger = setup_logging("DemandForecasting", config.app.log_level)


class ForecastConfig:
    """Configuration for Prophet forecasting."""
    
    def __init__(
        self,
        horizon_days: int = 30,
        confidence_level: float = 0.95,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False
    ):
        self.horizon_days = horizon_days
        self.confidence_level = confidence_level
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if not 7 <= self.horizon_days <= 365:
            raise ValidationError("Forecast horizon must be between 7 and 365 days")
        
        if not 0.80 <= self.confidence_level <= 0.99:
            raise ValidationError("Confidence level must be between 80% and 99%")
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'horizon_days': self.horizon_days,
            'confidence_level': self.confidence_level,
            'yearly_seasonality': self.yearly_seasonality,
            'weekly_seasonality': self.weekly_seasonality,
            'daily_seasonality': self.daily_seasonality
        }


class ForecastMetrics:
    """Metrics for evaluating forecast quality."""
    
    def __init__(self, historical_df: pd.DataFrame, forecast_df: pd.DataFrame):
        self.historical = historical_df
        self.forecast = forecast_df
    
    def calculate_mape(self) -> float:
        """Calculate Mean Absolute Percentage Error."""
        try:
            # Get overlapping dates
            merged = pd.merge(
                self.historical, 
                self.forecast[['ds', 'yhat']], 
                on='ds', 
                how='inner'
            )
            
            if len(merged) == 0:
                return 0.0
            
            actual = merged['y']
            predicted = merged['yhat']
            
            # Avoid division by zero
            mask = actual != 0
            mape = (abs((actual[mask] - predicted[mask]) / actual[mask])).mean() * 100
            
            return round(mape, 2)
            
        except Exception as e:
            logger.error(f"MAPE calculation failed: {e}")
            return 0.0
    
    def calculate_rmse(self) -> float:
        """Calculate Root Mean Square Error."""
        try:
            merged = pd.merge(
                self.historical, 
                self.forecast[['ds', 'yhat']], 
                on='ds', 
                how='inner'
            )
            
            if len(merged) == 0:
                return 0.0
            
            actual = merged['y']
            predicted = merged['yhat']
            
            rmse = ((actual - predicted) ** 2).mean() ** 0.5
            return round(rmse, 2)
            
        except Exception as e:
            logger.error(f"RMSE calculation failed: {e}")
            return 0.0
    
    def get_summary(self) -> Dict[str, float]:
        """Get summary of all metrics."""
        return {
            'mape': self.calculate_mape(),
            'rmse': self.calculate_rmse(),
            'data_points': len(self.historical)
        }


class SalesDataService:
    """Service for fetching sales data from Unity Catalog."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_historical_sales(
        _self,
        warehouse: str = "All",
        days_back: int = 365
    ) -> pd.DataFrame:
        """Fetch historical sales data."""
        logger.info(f"Fetching {days_back} days of sales data for {warehouse}")
        
        try:
            # Build warehouse filter
            warehouse_filter = ""
            if warehouse != "All":
                warehouse_filter = f"AND w.WarehouseName = '{warehouse}'"
            
            query = f"""
                SELECT 
                    DATE(s.SalesDate) as ds,
                    SUM(s.Quantity) as y
                FROM {config.unity_catalog.catalog}.silver.fact_sales s
                JOIN {config.unity_catalog.catalog}.silver.dim_warehouse w 
                    ON s.WarehouseSK = w.WarehouseSK
                WHERE s.SalesDate >= DATE_SUB(CURRENT_DATE(), {days_back})
                    {warehouse_filter}
                GROUP BY DATE(s.SalesDate)
                HAVING SUM(s.Quantity) > 0
                ORDER BY ds
            """
            
            with _self.db_manager.unity_catalog_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            
            if not rows:
                logger.warning("No sales data found")
                return pd.DataFrame(columns=['ds', 'y'])
            
            df = pd.DataFrame(rows, columns=columns)
            df['ds'] = pd.to_datetime(df['ds'])
            
            logger.info(f"Fetched {len(df)} data points")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch sales data: {e}")
            st.error(f"❌ Failed to load sales data: {str(e)}")
            return pd.DataFrame(columns=['ds', 'y'])
    
    @st.cache_data(ttl=3600)
    def get_warehouses(_self) -> List[str]:
        """Get list of available warehouses."""
        try:
            query = f"""
                SELECT DISTINCT WarehouseName
                FROM {config.unity_catalog.catalog}.silver.dim_warehouse
                ORDER BY WarehouseName
            """
            
            with _self.db_manager.unity_catalog_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            warehouses = ["All"] + [row[0] for row in rows if row[0]]
            return warehouses
            
        except Exception as e:
            logger.error(f"Failed to fetch warehouses: {e}")
            return ["All"]


class ForecastService:
    """Service for managing Prophet forecasts."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    @handle_errors("Forecasting failed")
    def run_forecast(
        self,
        historical_df: pd.DataFrame,
        forecast_config: ForecastConfig
    ) -> Tuple[pd.DataFrame, Prophet]:
        """Run Prophet forecast with given configuration."""
        
        if len(historical_df) < 14:
            raise ValidationError(
                "Insufficient data for forecasting. Need at least 14 days of history."
            )
        
        logger.info(f"Running forecast for {forecast_config.horizon_days} days")
        
        try:
            # Configure Prophet
            model = Prophet(
                interval_width=forecast_config.confidence_level,
                yearly_seasonality=forecast_config.yearly_seasonality,
                weekly_seasonality=forecast_config.weekly_seasonality,
                daily_seasonality=forecast_config.daily_seasonality
            )
            
            # Fit model
            with st.spinner("Training Prophet model..."):
                model.fit(historical_df)
            
            # Make forecast
            future = model.make_future_dataframe(periods=forecast_config.horizon_days)
            forecast = model.predict(future)
            
            logger.info("Forecast completed successfully")
            return forecast, model
            
        except Exception as e:
            logger.error(f"Prophet forecasting failed: {e}")
            raise
    
    @handle_errors("Failed to save forecast")
    def save_forecast_run(
        self,
        warehouse: str,
        forecast_config: ForecastConfig,
        metrics: Dict[str, float],
        run_by: str = "analyst"
    ) -> Optional[int]:
        """Save forecast run to Lakebase for audit trail."""
        
        try:
            with self.db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO forecast_runs (
                        warehouse_name,
                        product_category,
                        forecast_horizon_days,
                        confidence_level,
                        model_config,
                        mape,
                        rmse,
                        data_points,
                        run_by,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING run_id
                """, (
                    warehouse,
                    "All Products",
                    forecast_config.horizon_days,
                    int(forecast_config.confidence_level * 100),
                    json.dumps(forecast_config.to_dict()),
                    metrics.get('mape', 0),
                    metrics.get('rmse', 0),
                    metrics.get('data_points', 0),
                    run_by,
                    datetime.now()
                ))
                
                run_id = cursor.fetchone()[0]
            
            logger.info(f"Saved forecast run {run_id}")
            return run_id
            
        except Exception as e:
            logger.error(f"Failed to save forecast run: {e}")
            raise
    
    @st.cache_data(ttl=60)
    def get_recent_runs(_self, limit: int = 10) -> pd.DataFrame:
        """Get recent forecast runs."""
        try:
            with _self.db_manager.lakebase_cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        run_id,
                        warehouse_name,
                        forecast_horizon_days,
                        confidence_level,
                        mape,
                        rmse,
                        data_points,
                        run_by,
                        created_at
                    FROM forecast_runs
                    ORDER BY created_at DESC
                    LIMIT {limit}
                """)
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            
            if rows:
                return pd.DataFrame(rows, columns=columns)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to fetch forecast runs: {e}")
            return pd.DataFrame()


def render_header():
    """Render application header."""
    st.title("📈 Demand Forecasting Dashboard")
    st.markdown("**ML-Powered Predictions | Prophet Model | Production System**")
    st.markdown("---")


def render_forecast_config_sidebar(warehouses: List[str]) -> Tuple[str, ForecastConfig]:
    """Render sidebar configuration."""
    with st.sidebar:
        st.header("⚙️ Forecast Configuration")
        
        # Warehouse selection
        warehouse = st.selectbox(
            "Warehouse",
            warehouses,
            help="Select warehouse for demand forecast"
        )
        
        # Horizon
        horizon_days = st.slider(
            "Forecast Horizon (days)",
            min_value=7,
            max_value=90,
            value=30,
            help="Number of days to forecast into the future"
        )
        
        # Confidence level
        confidence = st.slider(
            "Confidence Level (%)",
            min_value=80,
            max_value=99,
            value=95,
            help="Confidence interval for predictions"
        ) / 100
        
        # Seasonality
        st.markdown("**Seasonality:**")
        yearly = st.checkbox("Yearly", value=True)
        weekly = st.checkbox("Weekly", value=True)
        daily = st.checkbox("Daily", value=False)
        
        config = ForecastConfig(
            horizon_days=horizon_days,
            confidence_level=confidence,
            yearly_seasonality=yearly,
            weekly_seasonality=weekly,
            daily_seasonality=daily
        )
        
        return warehouse, config


def render_historical_data_section(df: pd.DataFrame):
    """Render historical data visualization."""
    st.subheader("📊 Historical Sales Data")
    
    if df.empty:
        st.warning("No historical data available")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Points", len(df))
    
    with col2:
        st.metric("Avg Daily Sales", f"{df['y'].mean():.0f}")
    
    with col3:
        st.metric("Max Daily Sales", f"{df['y'].max():.0f}")
    
    with col4:
        date_range = (df['ds'].max() - df['ds'].min()).days
        st.metric("Days of History", date_range)
    
    # Line chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines',
        name='Historical Sales',
        line=dict(color='#1f77b4')
    ))
    
    fig.update_layout(
        title="Historical Sales Trend",
        xaxis_title="Date",
        yaxis_title="Quantity",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_forecast_results(
    historical_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    model: Prophet,
    metrics: Dict[str, float]
):
    """Render forecast results and visualizations."""
    st.subheader("🔮 Forecast Results")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "MAPE (Accuracy)",
            f"{metrics.get('mape', 0):.2f}%",
            help="Mean Absolute Percentage Error (lower is better)"
        )
    
    with col2:
        st.metric(
            "RMSE",
            f"{metrics.get('rmse', 0):.2f}",
            help="Root Mean Square Error"
        )
    
    with col3:
        forecast_points = len(forecast_df[forecast_df['ds'] > historical_df['ds'].max()])
        st.metric("Forecast Points", forecast_points)
    
    # Forecast visualization
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=historical_df['ds'],
        y=historical_df['y'],
        mode='lines',
        name='Historical',
        line=dict(color='#1f77b4')
    ))
    
    # Forecast
    future_mask = forecast_df['ds'] > historical_df['ds'].max()
    fig.add_trace(go.Scatter(
        x=forecast_df[future_mask]['ds'],
        y=forecast_df[future_mask]['yhat'],
        mode='lines',
        name='Forecast',
        line=dict(color='#ff7f0e', dash='dash')
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=forecast_df[future_mask]['ds'],
        y=forecast_df[future_mask]['yhat_upper'],
        mode='lines',
        name='Upper Bound',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_df[future_mask]['ds'],
        y=forecast_df[future_mask]['yhat_lower'],
        mode='lines',
        name='Lower Bound',
        line=dict(width=0),
        fillcolor='rgba(255, 127, 14, 0.2)',
        fill='tonexty',
        showlegend=True
    ))
    
    fig.update_layout(
        title="Sales Forecast with Confidence Interval",
        xaxis_title="Date",
        yaxis_title="Quantity",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Components
    with st.expander("📊 Forecast Components (Trend & Seasonality)"):
        fig_components = model.plot_components(forecast_df)
        st.pyplot(fig_components)


def render_forecast_history(forecast_service: ForecastService):
    """Render forecast run history."""
    st.subheader("📜 Forecast History")
    
    df = forecast_service.get_recent_runs(limit=20)
    
    if df.empty:
        st.info("No forecast history available")
        return
    
    # Format dates
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(
        df[['run_id', 'warehouse_name', 'forecast_horizon_days', 'mape', 'rmse', 'created_at']],
        use_container_width=True,
        hide_index=True
    )


def main():
    """Main application entry point."""
    try:
        # Initialize services
        db_manager = get_database_manager(config)
        sales_service = SalesDataService(db_manager)
        forecast_service = ForecastService(db_manager)
        
        # Render header
        render_header()
        
        # Get warehouses
        warehouses = sales_service.get_warehouses()
        
        # Sidebar configuration
        warehouse, forecast_config = render_forecast_config_sidebar(warehouses)
        
        # Validate configuration
        try:
            forecast_config.validate()
        except ValidationError as e:
            st.error(f"❌ Invalid configuration: {e.user_message}")
            return
        
        # Run forecast button
        run_forecast = st.sidebar.button("🚀 Run Forecast", type="primary")
        
        # Load historical data
        with st.spinner("Loading historical sales data..."):
            historical_df = sales_service.get_historical_sales(warehouse, days_back=365)
        
        if historical_df.empty:
            st.error("❌ No historical data available")
            return
        
        # Render historical data
        render_historical_data_section(historical_df)
        
        st.markdown("---")
        
        # Run forecast if requested
        if run_forecast:
            try:
                # Run forecast
                forecast_df, model = forecast_service.run_forecast(historical_df, forecast_config)
                
                # Calculate metrics
                metrics_calc = ForecastMetrics(historical_df, forecast_df)
                metrics = metrics_calc.get_summary()
                
                # Save to Lakebase
                run_id = forecast_service.save_forecast_run(
                    warehouse,
                    forecast_config,
                    metrics
                )
                
                if run_id:
                    st.success(f"✅ Forecast completed! Run ID: {run_id}")
                
                # Render results
                render_forecast_results(historical_df, forecast_df, model, metrics)
                
                # Clear cache to refresh history
                st.cache_data.clear()
                
            except Exception as e:
                logger.exception("Forecast failed")
                st.error(f"❌ Forecast failed: {str(e)}")
        
        # Forecast history
        st.markdown("---")
        render_forecast_history(forecast_service)
        
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
