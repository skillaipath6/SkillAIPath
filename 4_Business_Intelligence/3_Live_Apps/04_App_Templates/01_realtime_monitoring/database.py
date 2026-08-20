"""Database Connection"""
import pandas as pd
from databricks import sql
from typing import Optional, List
import streamlit as st

class Database:
    def __init__(self, config):
        self.config = config
        self._connection = None
    
    @property
    def connection(self):
        if self._connection is None:
            self._connection = sql.connect(
                server_hostname=self.config.DATABRICKS_SERVER_HOSTNAME,
                http_path=self.config.DATABRICKS_HTTP_PATH,
                access_token=self.config.DATABRICKS_TOKEN
            )
        return self._connection
    
    @st.cache_data(ttl=300)
    def get_inventory_metrics(_self, warehouse: Optional[str] = None) -> dict:
        query = f"""
        SELECT
            COALESCE(SUM(inventory_value), 0) as total_value,
            COUNT(DISTINCT product_id) as total_products,
            SUM(CASE WHEN stock_status = 'Critical' THEN 1 ELSE 0 END) as critical_items,
            ROUND(AVG(CASE WHEN current_stock = 0 THEN 100.0 ELSE 0.0 END), 1) as out_of_stock_pct
        FROM {_self.config.full_table_name('fact_inventory')}
        WHERE 1=1
        """
        if warehouse:
            query += f" AND warehouse_name = '{warehouse}'"
        
        with _self.connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return {
                'total_value': result[0] or 0,
                'total_products': result[1] or 0,
                'critical_items': result[2] or 0,
                'out_of_stock_pct': result[3] or 0.0
            }
    
    @st.cache_data(ttl=300)
    def get_warehouses(_self) -> List[str]:
        query = f"SELECT DISTINCT warehouse_name FROM {_self.config.full_table_name('fact_inventory')} ORDER BY warehouse_name"
        with _self.connection.cursor() as cursor:
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]
    
    @st.cache_data(ttl=300)
    def get_reorder_recommendations(_self, warehouse: Optional[str] = None, urgency_levels: List[str] = None) -> pd.DataFrame:
        query = f"""
        SELECT 
            warehouse_name, product_name, current_stock, reorder_point,
            recommended_qty, urgency, estimated_cost, days_until_stockout
        FROM {_self.config.full_table_name('fact_reorder_recommendations')}
        WHERE 1=1
        """
        if warehouse:
            query += f" AND warehouse_name = '{warehouse}'"
        if urgency_levels:
            levels = ",".join([f"'{u}'" for u in urgency_levels])
            query += f" AND urgency IN ({levels})"
        query += " ORDER BY urgency DESC, days_until_stockout ASC"
        
        with _self.connection.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(cursor.fetchall(), columns=columns)
    
    @st.cache_data(ttl=300)
    def get_warehouse_summary(_self) -> pd.DataFrame:
        query = f"""
        SELECT warehouse_name, SUM(inventory_value) as total_inventory_value
        FROM {_self.config.full_table_name('fact_inventory')}
        GROUP BY warehouse_name
        ORDER BY total_inventory_value DESC
        """
        with _self.connection.cursor() as cursor:
            cursor.execute(query)
            return pd.DataFrame(cursor.fetchall(), columns=['warehouse_name', 'total_inventory_value'])
    
    @st.cache_data(ttl=300)
    def get_status_distribution(_self, warehouse: Optional[str] = None) -> pd.DataFrame:
        query = f"""
        SELECT stock_status, COUNT(*) as count
        FROM {_self.config.full_table_name('fact_inventory')}
        WHERE 1=1
        """
        if warehouse:
            query += f" AND warehouse_name = '{warehouse}'"
        query += " GROUP BY stock_status"
        
        with _self.connection.cursor() as cursor:
            cursor.execute(query)
            return pd.DataFrame(cursor.fetchall(), columns=['stock_status', 'count'])
