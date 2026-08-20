"""Shared Infrastructure Package

Production-grade utilities for LiveApps:
- config: Configuration management
- db_manager: Database connection pooling
- error_handlers: Error handling utilities
- validators: Input validation
- logger: Structured logging
- lakebase_config: Lakebase connection manager
"""

from .config import config, Configuration
from .db_manager import DatabaseManager, get_database_manager
from .error_handlers import handle_errors, ValidationError, DatabaseOperationError
from .validators import Validator, ValidationResult
from .logger import setup_logging, AppLogger
from .lakebase_config import lakebase, LakebaseConnection

__all__ = [
    'config',
    'Configuration',
    'DatabaseManager',
    'get_database_manager',
    'handle_errors',
    'ValidationError',
    'DatabaseOperationError',
    'Validator',
    'ValidationResult',
    'setup_logging',
    'AppLogger',
    'lakebase',
    'LakebaseConnection'
]

__version__ = '2.0.0'
