"""
SkillAIPath - Database Connection Manager
Handles all database operations and query execution
"""

import pandas as pd
from databricks import sql
from typing import Optional
from config import config
import streamlit as st

class DatabaseManager:
    """Manages Databricks SQL connections and queries"""
    
    def __init__(self):
        self.catalog = config.database.catalog
        self.schema = config.database.schema_gold
        self._connection = None
    
    def get_connection(self):
        """Get or create database connection"""
        if self._connection is None:
            try:
                self._connection = sql.connect(
                    server_hostname=config.database.server_hostname,
                    http_path=config.database.http_path,
                    access_token=config.database.access_token
                )
            except Exception as e:
                st.error(f"Failed to connect to database: {e}")
                return None
        return self._connection
    
    @st.cache_data(ttl=300)
    def execute_query(_self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            DataFrame with query results
        """
        conn = _self.get_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or {})
            df = cursor.fetchall_arrow().to_pandas()
            cursor.close()
            return df
        except Exception as e:
            st.error(f"Query execution failed: {e}")
            return pd.DataFrame()
    
    def get_table_full_name(self, table_name: str) -> str:
        """Get fully qualified table name"""
        return f"{self.catalog}.{self.schema}.{table_name}"
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test database connection"""
        try:
            conn = self.get_connection()
            if not conn:
                return False, "Failed to establish connection"
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

# Global database manager instance
db_manager = DatabaseManager()
