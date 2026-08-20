"""
SkillAIPath - Gold Analytics Configuration
Centralized configuration management
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    server_hostname: str
    http_path: str
    access_token: str
    catalog: str = "sap_dev"
    schema_gold: str = "sap_gold"
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME", ""),
            http_path=os.getenv("DATABRICKS_HTTP_PATH", ""),
            access_token=os.getenv("DATABRICKS_TOKEN", ""),
            catalog=os.getenv("DATABRICKS_CATALOG", "sap_dev"),
            schema_gold=os.getenv("DATABRICKS_SCHEMA_GOLD", "sap_gold")
        )
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate configuration"""
        if not self.server_hostname:
            return False, "DATABRICKS_SERVER_HOSTNAME is required"
        if not self.http_path:
            return False, "DATABRICKS_HTTP_PATH is required"
        if not self.access_token:
            return False, "DATABRICKS_TOKEN is required"
        return True, None

@dataclass
class AppConfig:
    """Application configuration"""
    port: int = 8080
    log_level: str = "INFO"
    cache_ttl: int = 300
    max_rows: int = 10000
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            port=int(os.getenv("APP_PORT", "8080")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            cache_ttl=int(os.getenv("CACHE_TTL_SECONDS", "300")),
            max_rows=int(os.getenv("MAX_ROWS_PER_QUERY", "10000"))
        )

class Config:
    """Master configuration"""
    def __init__(self):
        self.database = DatabaseConfig.from_env()
        self.app = AppConfig.from_env()
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate all configurations"""
        return self.database.validate()

# Global config instance
config = Config()
