"""Pytest configuration"""
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ['DATABRICKS_SERVER_HOSTNAME'] = 'test-workspace.cloud.databricks.com'
    os.environ['DATABRICKS_HTTP_PATH'] = '/sql/1.0/warehouses/test'
    os.environ['DATABRICKS_TOKEN'] = 'test-token'
    os.environ['API_TOKENS'] = 'demo-token-123,demo-token-456'
    os.environ['DATABRICKS_CATALOG'] = 'sap_catalog'
    os.environ['DATABRICKS_SCHEMA'] = 'sap_silver'
