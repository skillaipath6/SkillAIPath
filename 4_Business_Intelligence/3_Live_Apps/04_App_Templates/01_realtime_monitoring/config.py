"""Configuration Management"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Config:
    DATABRICKS_SERVER_HOSTNAME: str = os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
    DATABRICKS_HTTP_PATH: str = os.getenv("DATABRICKS_HTTP_PATH", "")
    DATABRICKS_TOKEN: str = os.getenv("DATABRICKS_TOKEN", "")
    CATALOG: str = "sap"
    SCHEMA: str = "inventory_management"
    
    def __post_init__(self):
        if not self.DATABRICKS_TOKEN:
            raise ValueError("DATABRICKS_TOKEN not set")
    
    def full_table_name(self, table: str) -> str:
        return f"{self.CATALOG}.{self.SCHEMA}.{table}"
