"""Production Configuration Management

Centralized configuration with environment-based settings and validation.
"""

import os
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LakebaseConfig:
    """Lakebase Postgres configuration."""
    project: str
    branch: str
    endpoint: str
    host: str
    port: int = 5432
    database: str = "databricks_postgres"


@dataclass
class UnityCatalogConfig:
    """Unity Catalog connection configuration."""
    server_hostname: str
    http_path: str
    catalog: str = "sap_dev"
    

@dataclass
class AppConfig:
    """Main application configuration."""
    app_name: str
    environment: str
    debug: bool
    log_level: str
    

class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Configuration:
    """Central configuration manager with validation."""
    
    def __init__(self):
        self._lakebase: Optional[LakebaseConfig] = None
        self._unity_catalog: Optional[UnityCatalogConfig] = None
        self._app: Optional[AppConfig] = None
    
    @property
    def lakebase(self) -> LakebaseConfig:
        """Get Lakebase configuration."""
        if not self._lakebase:
            self._lakebase = LakebaseConfig(
                project="retail-ops-apps",
                branch="production",
                endpoint="projects/retail-ops-apps/branches/production/endpoints/primary",
                host="ep-dark-lab-d8hwsb07.database.us-east-2.cloud.databricks.com",
                port=5432,
                database="databricks_postgres"
            )
        return self._lakebase
    
    @property
    def unity_catalog(self) -> UnityCatalogConfig:
        """Get Unity Catalog configuration."""
        if not self._unity_catalog:
            hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
            http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
            
            self._unity_catalog = UnityCatalogConfig(
                server_hostname=hostname,
                http_path=http_path,
                catalog="sap_dev"
            )
        return self._unity_catalog
    
    @property
    def app(self) -> AppConfig:
        """Get application configuration."""
        if not self._app:
            self._app = AppConfig(
                app_name=os.getenv("APP_NAME", "LiveApp"),
                environment=os.getenv("ENVIRONMENT", "production"),
                debug=os.getenv("DEBUG", "false").lower() == "true",
                log_level=os.getenv("LOG_LEVEL", "INFO")
            )
        return self._app
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment.lower() == "production"


# Global configuration instance
config = Configuration()
