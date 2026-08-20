"""Input Validation Utilities

Comprehensive validation for user inputs and business logic.
"""

from typing import Optional, List
from datetime import datetime, timedelta
import re


class ValidationResult:
    """Result of a validation check."""
    def __init__(self, is_valid: bool, message: str = ""):
        self.is_valid = is_valid
        self.message = message
    
    def __bool__(self):
        return self.is_valid


class Validator:
    """Validation utilities for common inputs."""
    
    @staticmethod
    def validate_quantity(qty: int, min_value: int = 1, max_value: int = 1000000) -> ValidationResult:
        """Validate inventory quantity."""
        if not isinstance(qty, (int, float)):
            return ValidationResult(False, "Quantity must be a number")
        
        if qty < min_value:
            return ValidationResult(False, f"Quantity must be at least {min_value}")
        
        if qty > max_value:
            return ValidationResult(False, f"Quantity cannot exceed {max_value:,}")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_percentage(pct: float, min_val: float = -100, max_val: float = 100) -> ValidationResult:
        """Validate percentage value."""
        if not isinstance(pct, (int, float)):
            return ValidationResult(False, "Percentage must be a number")
        
        if pct < min_val or pct > max_val:
            return ValidationResult(False, f"Percentage must be between {min_val}% and {max_val}%")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime, max_days: int = 365) -> ValidationResult:
        """Validate date range."""
        if start_date > end_date:
            return ValidationResult(False, "Start date must be before end date")
        
        delta = (end_date - start_date).days
        if delta > max_days:
            return ValidationResult(False, f"Date range cannot exceed {max_days} days")
        
        if delta < 1:
            return ValidationResult(False, "Date range must be at least 1 day")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_product_name(name: str) -> ValidationResult:
        """Validate product name."""
        if not name or not name.strip():
            return ValidationResult(False, "Product name cannot be empty")
        
        if len(name) > 200:
            return ValidationResult(False, "Product name too long (max 200 characters)")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return ValidationResult(False, "Invalid email format")
        
        return ValidationResult(True)


def sanitize_sql_input(value: str) -> str:
    """Sanitize input to prevent SQL injection."""
    # Remove dangerous characters
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
    sanitized = value
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    return sanitized.strip()
