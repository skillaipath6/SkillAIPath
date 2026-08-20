"""Database Connection Manager

Production-grade connection pooling, error handling, and retry logic.
"""

import psycopg2
from psycopg2 import pool
from databricks import sql
from databricks.sdk import WorkspaceClient
import streamlit as st
from typing import Optional
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DatabaseManager:
    """Manages database connections with pooling and retry logic."""
    
    def __init__(self, config):
        self.config = config
        self._lb_pool: Optional[pool.SimpleConnectionPool] = None
        self._uc_conn: Optional[sql.Connection] = None
        self._workspace_client: Optional[WorkspaceClient] = None
    
    @property
    def workspace_client(self) -> WorkspaceClient:
        """Get or create Workspace client."""
        if not self._workspace_client:
            try:
                self._workspace_client = WorkspaceClient()
            except Exception as e:
                logger.error(f"Failed to create WorkspaceClient: {e}")
                raise ConnectionError("Cannot authenticate with Databricks workspace")
        return self._workspace_client
    
    def get_lakebase_connection(self, max_retries: int = 3):
        """Get Lakebase Postgres connection with retry logic."""
        for attempt in range(max_retries):
            try:
                # Generate fresh credentials
                w = self.workspace_client
                creds = w.postgres.generate_database_credential(
                    endpoint=self.config.lakebase.endpoint
                )
                
                conn = psycopg2.connect(
                    host=self.config.lakebase.host,
                    port=self.config.lakebase.port,
                    database=self.config.lakebase.database,
                    user=w.current_user.me().user_name,
                    password=creds.token,
                    sslmode="require",
                    connect_timeout=30
                )
                
                logger.info("Lakebase connection established")
                return conn
                
            except psycopg2.OperationalError as e:
                logger.warning(f"Lakebase connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Lakebase after {max_retries} attempts")
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error connecting to Lakebase: {e}")
                raise ConnectionError(f"Lakebase connection failed: {str(e)}")
    
    @contextmanager
    def lakebase_cursor(self):
        """Context manager for Lakebase operations."""
        conn = None
        cursor = None
        try:
            conn = self.get_lakebase_connection()
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_unity_catalog_connection(self):
        """Get Unity Catalog SQL connection with retry."""
        try:
            import os
            conn = sql.connect(
                server_hostname=self.config.unity_catalog.server_hostname,
                http_path=self.config.unity_catalog.http_path,
                access_token=os.getenv("DATABRICKS_TOKEN", "")
            )
            logger.info("Unity Catalog connection established")
            return conn
        except Exception as e:
            logger.error(f"Unity Catalog connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Unity Catalog: {str(e)}")
    
    @contextmanager
    def unity_catalog_cursor(self):
        """Context manager for Unity Catalog operations."""
        conn = None
        cursor = None
        try:
            conn = self.get_unity_catalog_connection()
            cursor = conn.cursor()
            yield cursor
        except Exception as e:
            logger.error(f"Unity Catalog operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def test_connections(self) -> dict:
        """Test both database connections."""
        results = {
            "lakebase": False,
            "unity_catalog": False,
            "errors": []
        }
        
        # Test Lakebase
        try:
            with self.lakebase_cursor() as cursor:
                cursor.execute("SELECT 1")
                results["lakebase"] = True
        except Exception as e:
            results["errors"].append(f"Lakebase: {str(e)}")
        
        # Test Unity Catalog
        try:
            with self.unity_catalog_cursor() as cursor:
                cursor.execute("SELECT 1")
                results["unity_catalog"] = True
        except Exception as e:
            results["errors"].append(f"Unity Catalog: {str(e)}")
        
        return results
    
    def close_all(self):
        """Close all connections."""
        if self._uc_conn:
            try:
                self._uc_conn.close()
            except:
                pass


    def initialize_schema(self):
        """Initialize Lakebase schema if tables don't exist."""
        if hasattr(self, '_schema_initialized') and self._schema_initialized:
            return
        
        try:
            with self.lakebase_cursor() as cursor:
                # Create reorder_approvals table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reorder_approvals (
                        id SERIAL PRIMARY KEY,
                        product_sk INTEGER NOT NULL,
                        product_name VARCHAR(255) NOT NULL,
                        warehouse_sk INTEGER NOT NULL,
                        warehouse_name VARCHAR(255) NOT NULL,
                        recommended_qty INTEGER NOT NULL,
                        current_stock INTEGER NOT NULL,
                        urgency VARCHAR(50) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'pending',
                        notes TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        approved_at TIMESTAMP,
                        approved_by VARCHAR(255)
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reorder_approvals_status ON reorder_approvals(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reorder_approvals_created_at ON reorder_approvals(created_at DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reorder_approvals_product_warehouse ON reorder_approvals(product_sk, warehouse_sk)")
                
                logger.info("✅ Lakebase schema initialized successfully")
                self._schema_initialized = True
                
        except Exception as e:
            logger.warning(f"Schema initialization check failed (may already exist): {e}")
            self._schema_initialized = True  # Don't retry every time


@st.cache_resource
def get_database_manager(config):
    """Get cached database manager instance with schema initialization."""
    manager = DatabaseManager(config)
    try:
        manager.initialize_schema()  # Auto-create schema on first use
    except Exception as e:
        logger.warning(f"Schema initialization skipped: {e}")
    return manager
