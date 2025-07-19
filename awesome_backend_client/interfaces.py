"""
Interfaces and abstract base classes for SOLID design
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Protocol


class IHTTPClient(Protocol):
    """Interface for HTTP clients"""

    async def get(
        self, endpoint: str, **kwargs: Any
    ) -> dict[str, Any] | list[dict[str, Any]] | str: ...

    async def post(
        self, endpoint: str, **kwargs: Any
    ) -> dict[str, Any] | list[dict[str, Any]] | str: ...

    async def put(
        self, endpoint: str, **kwargs: Any
    ) -> dict[str, Any] | list[dict[str, Any]] | str: ...

    async def delete(self, endpoint: str, **kwargs: Any) -> dict[str, Any] | str: ...

    async def close(self) -> None: ...


class IWebSocketClient(Protocol):
    """Interface for WebSocket clients"""

    async def connect(self) -> bool: ...

    async def disconnect(self) -> None: ...

    def add_listener(self, event: str, callback: Callable) -> None: ...

    def remove_listener(self, event: str, callback: Callable) -> None: ...

    async def subscribe_events(self, events: list[str]) -> bool: ...

    @property
    def is_connected(self) -> bool: ...


class IEventManager(Protocol):
    """Interface for event management"""

    def add_listener(self, event: str, callback: Callable) -> None: ...

    def remove_listener(self, event: str, callback: Callable) -> None: ...

    async def emit(self, event: str, data: Any) -> None: ...

    def get_listeners(self, event: str) -> list[Callable]: ...


class ICRUDManager(Protocol):
    """Interface for CRUD managers"""

    async def list(self, **kwargs: Any) -> list[dict[str, Any]]: ...

    async def get(self, item_id: int | str) -> dict[str, Any]: ...

    async def create(self, data: dict[str, Any]) -> dict[str, Any]: ...

    async def update(
        self, item_id: int | str, data: dict[str, Any]
    ) -> dict[str, Any]: ...

    async def delete(self, item_id: int | str) -> None: ...


class ISettings(Protocol):
    """Interface for settings"""

    @property
    def BACKEND_API_KEY(self) -> str: ...

    @property
    def FULL_API_URL(self) -> str: ...

    @property
    def WEBSOCKET_ENABLED(self) -> bool: ...


class BaseResourceManager(ABC):
    """Abstract base class for resource managers (LSP compliance)"""

    def __init__(self, http_client: IHTTPClient, resource_name: str) -> None:
        self._http_client = http_client
        self._resource_name = resource_name
        self._endpoint = f"/{resource_name}"

    @abstractmethod
    async def list(self, **kwargs: Any) -> list[dict[str, Any]]:
        """List resources"""

    @abstractmethod
    async def get(self, item_id: int | str) -> dict[str, Any]:
        """Get resource by ID"""

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create resource"""

    @abstractmethod
    async def update(self, item_id: int | str, data: dict[str, Any]) -> dict[str, Any]:
        """Update resource"""

    @abstractmethod
    async def delete(self, item_id: int | str) -> None:
        """Delete resource"""


class EventHandler(ABC):
    """Abstract base class for event handlers"""

    @abstractmethod
    async def handle(self, event_data: Any) -> None:
        """Handle event"""

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Event type this handler processes"""


class IClientFactory(Protocol):
    """Factory interface for creating clients"""

    def create_http_client(self, **kwargs: Any) -> IHTTPClient: ...

    def create_websocket_client(self, **kwargs: Any) -> IWebSocketClient: ...

    def create_event_manager(self, **kwargs: Any) -> IEventManager: ...


class IServiceLocator(Protocol):
    """Service locator interface for dependency injection"""

    def get_service(self, service_type: type) -> Any: ...

    def register_service(self, service_type: type, service_instance: Any) -> None: ...


# Type aliases for better readability
EventCallback = Callable[[Any], None]
AsyncEventCallback = Callable[[Any], Any]  # Can be sync or async
EventData = dict[str, Any]
ResourceData = dict[str, Any]
