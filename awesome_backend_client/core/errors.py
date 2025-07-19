"""
Core error classes for the UAProject Backend Client.

These errors are raised by the client when API calls fail.
Built on top of awesome-errors for consistent error handling.
"""

from awesome_errors import BackendError


class APIError(Exception):
    """Base exception for all API errors"""

    def __init__(self, message: str, endpoint: str | None = None) -> None:
        self.message = message
        self.endpoint = endpoint
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.endpoint:
            return f"{self.message} (endpoint: {self.endpoint})"
        return self.message


class APIConnectionError(APIError):
    """Raised when connection to API fails"""

    def __init__(
        self,
        message: str,
        endpoint: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, endpoint)
        self.status_code = status_code


class APIAuthenticationError(APIError):
    """Raised when authentication fails (401)"""


class APIPermissionError(APIError):
    """Raised when user lacks permissions (403)"""


class APIRateLimitError(APIError):
    """Raised when rate limit is exceeded (429)"""

    def __init__(
        self,
        endpoint: str,
        retry_after: int | None = None,
    ) -> None:
        message = f"Rate limit exceeded for {endpoint}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, endpoint)
        self.retry_after = retry_after


class APIServerError(APIError):
    """Raised when server returns 5xx error"""

    def __init__(self, endpoint: str, status_code: int, message: str) -> None:
        super().__init__(message, endpoint)
        self.status_code = status_code


class ConfigurationError(Exception):
    """Raised when client configuration is invalid"""


# Re-export BackendError for convenience
__all__ = [
    "APIAuthenticationError",
    "APIConnectionError",
    "APIError",
    "APIPermissionError",
    "APIRateLimitError",
    "APIServerError",
    "BackendError",  # From awesome-errors
    "ConfigurationError",
]
