"""Enhanced error handling with awesome-errors integration"""

from typing import Any, Optional

# Import awesome-errors classes
from awesome_errors import (
    AuthError,
    BackendError,
    BusinessLogicError,
    DatabaseError,
    ErrorResponseParser,
    NotFoundError,
    ValidationError,
)


# Client-specific exceptions that extend awesome-errors
class CRUDNotFoundError(NotFoundError):
    """Raised when a requested resource is not found"""

    def __init__(self, model: str, obj_id: Any = None, detail: Optional[str] = None):
        self.model = model
        self.obj_id = obj_id

        if detail:
            message = detail
        elif obj_id is not None:
            message = f"{model} with id {obj_id} not found"
        else:
            message = f"{model} not found"

        super().__init__(message, resource=model, resource_id=obj_id)


class CRUDValidationError(ValidationError):
    """Raised when validation fails"""

    def __init__(self, detail: str, field: Optional[str] = None):
        self.field = field
        super().__init__(detail, field=field)


class APIConnectionError(BackendError):
    """Raised when API connection fails"""

    def __init__(
        self,
        message: str,
        endpoint: str,
        status_code: Optional[int] = None,
        response_data: Optional[dict] = None,
    ):
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_data = response_data

        error_msg = f"API Error at {endpoint}"
        if status_code:
            error_msg += f" (Status: {status_code})"
        error_msg += f": {message}"

        super().__init__(error_msg)


class APIAuthenticationError(AuthError):
    """Raised when API authentication fails"""

    def __init__(self, endpoint: str, message: str = "Authentication failed"):
        super().__init__(message)
        self.endpoint = endpoint


class APIPermissionError(AuthError):
    """Raised when API permission is denied"""

    def __init__(self, endpoint: str, message: str = "Permission denied"):
        super().__init__(message)
        self.endpoint = endpoint


class APIRateLimitError(BackendError):
    """Raised when API rate limit is exceeded"""

    def __init__(self, endpoint: str, retry_after: Optional[int] = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message)
        self.endpoint = endpoint
        self.retry_after = retry_after


class APIServerError(DatabaseError):
    """Raised when API server returns 5xx error"""

    def __init__(self, endpoint: str, status_code: int, message: str = "Server error"):
        super().__init__(message)
        self.endpoint = endpoint
        self.status_code = status_code


class SerializationError(BackendError):
    """Raised when serialization/deserialization fails"""

    def __init__(self, message: str, data: Any = None):
        self.data = data
        super().__init__(message)


class ConfigurationError(BackendError):
    """Raised when configuration is invalid"""

    def __init__(self, message: str, setting_name: Optional[str] = None):
        self.setting_name = setting_name
        super().__init__(message)


class WebhookValidationError(ValidationError):
    """Raised when webhook validation fails"""

    def __init__(self, message: str, signature: Optional[str] = None):
        super().__init__(message)
        self.signature = signature


# Export awesome-errors classes for convenience
__all__ = [
    # awesome-errors classes
    "BackendError",
    "ErrorResponseParser",
    "NotFoundError",
    "ValidationError",
    "AuthError",
    "DatabaseError",
    "BusinessLogicError",
    # Client-specific exceptions
    "CRUDNotFoundError",
    "CRUDValidationError",
    "APIConnectionError",
    "APIAuthenticationError",
    "APIPermissionError",
    "APIRateLimitError",
    "APIServerError",
    "SerializationError",
    "ConfigurationError",
    "WebhookValidationError",
]
