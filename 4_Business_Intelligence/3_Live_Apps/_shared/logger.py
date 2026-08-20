"""Structured Logging Configuration

Production-grade logging with proper formatting and levels.
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class AppLogger:
    """Centralized logging configuration."""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, level: str = "INFO") -> logging.Logger:
        """Get or create a logger with consistent formatting."""
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Avoid duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def log_operation(cls, logger: logging.Logger, operation: str, **kwargs):
        """Log an operation with structured context."""
        context = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.info(f"{operation} - {context}")


def setup_logging(app_name: str, level: str = "INFO"):
    """Initialize logging for an application."""
    return AppLogger.get_logger(app_name, level)
