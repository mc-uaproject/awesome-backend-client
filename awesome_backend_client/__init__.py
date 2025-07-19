"""
Enhanced Python client library for interacting with the UAProject API Backend.

Provides convenient access to all API resources through CRUD services with
improved architecture following backend patterns.
"""

from .client import UAProjectClient
from .core import settings
from .core.errors import (
    APIAuthenticationError,
    APIConnectionError,
    APIPermissionError,
    APIRateLimitError,
    APIServerError,
    ConfigurationError,
)
from .events import (
    EventConfig,
    EventSource,
    UniversalEventManager,
)
from .fields import WebhookField
from .http import HTTPClient
from .logger import get_logger
from .models import User
from .payload import (
    DotDict,
    EventPayload,
    WebhookPayload,
    WebSocketPayload,
    create_payload,
)
from .webhooks import (
    WebhookConfig,
    WebhookRegistrar,
    WebhookSignatureValidator,
    WebhookTemplate,
)

__version__ = "2.0.0"

__all__ = [
    # Main Client (discord.py style)
    "UAProjectClient",
    # Models
    "User",
    # Core
    "HTTPClient",
    "settings",
    "get_logger",
    "WebhookField",
    # Webhook System
    "WebhookConfig",
    "WebhookRegistrar",
    "WebhookSignatureValidator",
    "WebhookTemplate",
    # Event System
    "EventSource",
    "EventConfig",
    "UniversalEventManager",
    # Payload System
    "DotDict",
    "EventPayload",
    "WebSocketPayload",
    "WebhookPayload",
    "create_payload",
    # Errors
    "APIConnectionError",
    "APIAuthenticationError",
    "APIPermissionError",
    "APIRateLimitError",
    "APIServerError",
    "ConfigurationError",
]
