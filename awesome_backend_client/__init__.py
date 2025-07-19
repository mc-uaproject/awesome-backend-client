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
    "APIAuthenticationError",
    # Errors
    "APIConnectionError",
    "APIPermissionError",
    "APIRateLimitError",
    "APIServerError",
    "ConfigurationError",
    # Payload System
    "DotDict",
    "EventConfig",
    "EventPayload",
    # Event System
    "EventSource",
    # Core
    "HTTPClient",
    # Main Client (discord.py style)
    "UAProjectClient",
    "UniversalEventManager",
    # Models
    "User",
    "WebSocketPayload",
    # Webhook System
    "WebhookConfig",
    "WebhookField",
    "WebhookPayload",
    "WebhookRegistrar",
    "WebhookSignatureValidator",
    "WebhookTemplate",
    "create_payload",
    "get_logger",
    "settings",
]
