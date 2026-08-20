"""Error Handling Utilities

Standardized error handling and user feedback.
"""

import streamlit as st
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, user_message: Optional[str] = None):
        self.message = message
        self.user_message = user_message or message
        super().__init__(self.message)


class ValidationError(AppError):
    """Input validation error."""
    pass


class DatabaseOperationError(AppError):
    """Database operation error."""
    pass


def handle_errors(user_message: str = "An error occurred"):
    """Decorator for error handling with user feedback."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"Validation error in {func.__name__}: {e}")
                st.error(f"❌ {e.user_message}")
                return None
            except DatabaseOperationError as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                st.error(f"❌ Database operation failed: {e.user_message}")
                return None
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}")
                st.error(f"❌ {user_message}: {str(e)}")
                return None
        return wrapper
    return decorator


def validate_positive_number(value: Any, field_name: str) -> int:
    """Validate that a value is a positive number."""
    try:
        num = int(value)
        if num <= 0:
            raise ValidationError(
                f"{field_name} must be positive",
                f"Please enter a positive number for {field_name}"
            )
        return num
    except (TypeError, ValueError):
        raise ValidationError(
            f"Invalid {field_name}",
            f"{field_name} must be a valid number"
        )


def validate_non_empty(value: str, field_name: str) -> str:
    """Validate that a string is non-empty."""
    if not value or not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            f"Please provide a value for {field_name}"
        )
    return value.strip()


def show_error_with_recovery(error: Exception, recovery_action: Optional[Callable] = None):
    """Show error with optional recovery action."""
    st.error(f"❌ {str(error)}")
    
    if recovery_action:
        if st.button("🔄 Retry"):
            try:
                recovery_action()
                st.success("✅ Operation completed successfully")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Retry failed: {str(e)}")
