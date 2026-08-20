"""Lakebase Postgres Configuration

Production-ready configuration with proper connection management.
"""

from databricks.sdk import WorkspaceClient
import psycopg2
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LakebaseConnection:
    """Manages Lakebase Postgres connections with credential refresh."""
    
    def __init__(self):
        self.project = "retail-ops-apps"
        self.branch = "production"
        self.endpoint = "projects/retail-ops-apps/branches/production/endpoints/primary"
        self.host = "ep-dark-lab-d8hwsb07.database.us-east-2.cloud.databricks.com"
        self.port = 5432
        self.database = "databricks_postgres"
        self._workspace_client: Optional[WorkspaceClient] = None
    
    @property
    def workspace_client(self) -> WorkspaceClient:
        """Get or create workspace client."""
        if not self._workspace_client:
            self._workspace_client = WorkspaceClient()
        return self._workspace_client
    
    def get_connection(self) -> psycopg2.extensions.connection:
        """Get a new database connection with fresh credentials."""
        try:
            w = self.workspace_client
            creds = w.postgres.generate_database_credential(endpoint=self.endpoint)
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=w.current_user.me().user_name,
                password=creds.token,
                sslmode="require",
                connect_timeout=30
            )
            
            logger.info(f"Lakebase connection established for {self.project}/{self.branch}")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to connect to Lakebase: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Global instance
lakebase = LakebaseConnection()
