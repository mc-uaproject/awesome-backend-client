"""
UAProject Backend Client - disnake style

Simple and clean API client for UAProject backend.
Uses existing backend patterns and schemas without duplication.
"""

import logging
from collections.abc import Callable
from typing import Any, Literal

from uaproject_backend_schemas.models import (
    User,
)

from .core.config import settings
from .events import BackwardCompatibilityDecorators, UniversalEventManager
from .http import APIResponse, HTTPClient
from .managers import (
    ApplicationManager,
    ApplicationSectionManager,
    BalanceManager,
    TransactionManager,
    UserManager,
)
from .webhooks import WebhookRegistrar
from .websocket import WebSocketClient

logger = logging.getLogger(__name__)


class UAProjectClient:
    """
    UAProject Backend Client - disnake style

    Simple to use:
        client = UAProjectClient()
        await client.start()

        user = await client.fetch_user(123)
        my_balance = await client.fetch_me_balance()

        # Or context manager
        async with UAProjectClient() as client:
            user = await client.fetch_user(123)

        # With events
        @client.event
        async def on_user_create(user):
            print(f"New user: {user.minecraft_nickname}")
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        impersonate_user_id: int | None = None,
        impersonate_discord_id: int | None = None,
    ):
        """Initialize UAProject client"""
        self.api_key = api_key or settings.BACKEND_API_KEY
        self.base_url = base_url or settings.FULL_API_URL
        self.impersonate_user_id = impersonate_user_id
        self.impersonate_discord_id = impersonate_discord_id

        # Internal state
        self._ready = False
        self._closed = False
        self._http_client: HTTPClient | None = None
        self._websocket: WebSocketClient | None = None

        # Universal Event System (NEW)
        self.events = UniversalEventManager(self)
        self._legacy_decorators = BackwardCompatibilityDecorators(self.events)

        # Legacy event system (for backward compatibility)
        self._listeners: dict[str, list[Callable[..., Any]]] = {}

        # Webhook system
        self.webhook_registrar = WebhookRegistrar(self)

        # Resource managers (discord.py style) - Universal CRUD for all resources
        self.users = UserManager(self)
        self.balances = BalanceManager(self)
        self.transactions = TransactionManager(self)
        self.applications = ApplicationManager(self)
        self.application_sections = ApplicationSectionManager(self)

        logger.debug(
            f"UAProjectClient initialized - impersonating: {impersonate_user_id}"
        )

    @property
    def http(self) -> HTTPClient:
        """Get HTTP client (lazy init)"""
        if self._http_client is None:
            self._http_client = HTTPClient(
                base_url=self.base_url,
                api_key=self.api_key,
                impersonate_user_id=self.impersonate_user_id,
                impersonate_discord_id=self.impersonate_discord_id,
            )
        return self._http_client

    # ==================== HTTP REQUEST METHODS ====================

    async def _request(
        self,
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        endpoint: str,
        **kwargs: Any,
    ) -> APIResponse:
        """Make HTTP request with error handling"""
        if method == "GET":
            return await self.http.get(endpoint, **kwargs)
        if method == "POST":
            return await self.http.post(endpoint, **kwargs)
        if method == "PUT":
            return await self.http.put(endpoint, **kwargs)
        if method == "PATCH":
            return await self.http.patch(endpoint, **kwargs)
        if method == "DELETE":
            return await self.http.delete(endpoint, **kwargs)
        msg = f"Unsupported HTTP method: {method}"
        raise ValueError(msg)

    # ==================== USER METHODS (discord.py style) ====================

    async def fetch_user(self, user_id: int) -> User | None:
        """Fetch user by ID (always from API, like discord.py fetch_user)"""
        data = await self.users.get(user_id)
        return User.model_validate(data)

    async def get_user(self, user_id: int) -> User | None:
        """Get user by ID (same as fetch_user since caching disabled)"""
        return await self.fetch_user(user_id)

    @property
    def user(self) -> UserManager:
        """Current user manager (like discord.py client.user)"""
        return self.users

    async def fetch_users(self, *, limit: int = 50, **filters: Any) -> list[User]:
        """Fetch multiple users"""
        data = await self.users.list(limit=limit, **filters)
        return [User.model_validate(user) for user in data]

    async def search_users(self, nickname: str, *, limit: int = 10) -> list[User]:
        """Search users by nickname"""
        data = await self.users.search_by_nickname(nickname, limit=limit)
        return [User.model_validate(user) for user in data]

    async def update_user(
        self, user_id: int | Literal["me"], **user_data: Any
    ) -> User | None:
        """Update user data. Use 'me' for current user"""
        data = await self.users.update(user_id, user_data)
        return User.model_validate(data)

    async def update_me(self, **user_data: Any) -> User | None:
        """Update current user data"""
        return await self.update_user("me", **user_data)

    # ==================== EVENT SYSTEM ====================

    def event(self, coro: Callable[..., Any]) -> Callable[..., Any]:
        """
        Legacy decorator for event handlers (discord.py style)

        Note: Use @client.events.on() for new code with more features

        Example:
            @client.event
            async def on_user_create(user):
                print(f"New user created: {user.minecraft_nickname}")
        """
        return self._legacy_decorators.event(coro)  # type: ignore[no-any-return]

    def listen(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Legacy decorator for event listeners with custom event names

        Note: Use @client.events.on() for new code with more features

        Example:
            @client.listen('user_create')
            async def handle_new_user(user):
                print(f"New user: {user.minecraft_nickname}")
        """
        return self._legacy_decorators.listen(name)  # type: ignore[no-any-return]

    # ==================== WEBHOOK METHODS ====================

    async def register_webhook_template(
        self, template_name: str, endpoint: str, **kwargs: Any
    ) -> Any:
        """Register a predefined webhook template"""
        return await self.webhook_registrar.register_template(
            template_name, endpoint, **kwargs
        )

    async def auto_register_webhooks(self, base_endpoint: str) -> Any:
        """Automatically register common webhooks"""
        return await self.webhook_registrar.auto_register_common_webhooks(base_endpoint)

    async def unregister_webhook(self, name: str) -> Any:
        """Unregister a webhook by name"""
        return await self.webhook_registrar.unregister_webhook(name)

    @property
    def registered_webhooks(self) -> dict[str, Any]:
        """Get registered webhooks"""
        return self.webhook_registrar.registered_webhooks

    async def handle_webhook_payload(self, payload: dict[str, Any]) -> Any:
        """Handle incoming webhook payload"""
        return await self.events.handle_webhook_payload(payload)

    def list_event_handlers(self) -> dict[str, Any]:
        """List all registered event handlers"""
        return self.events.list_handlers()

    def get_event_stats(self) -> dict[str, Any]:
        """Get event system statistics"""
        return self.events.get_stats()

    # ==================== WEBSOCKET METHODS ====================

    @property
    def websocket(self) -> WebSocketClient | None:
        """Get WebSocket client instance"""
        return self._websocket

    async def subscribe_events(self, events: list[str]) -> bool:
        """Subscribe to WebSocket events"""
        if self._websocket and self._websocket.is_connected:
            return bool(await self._websocket.subscribe_events(events))
        return False

    async def unsubscribe_events(self, events: list[str]) -> bool:
        """Unsubscribe from WebSocket events"""
        if self._websocket and self._websocket.is_connected:
            return bool(await self._websocket.unsubscribe_events(events))
        return False

    def add_event_listener(self, event: str, callback: Callable[..., Any]) -> None:
        """Add event listener for WebSocket events"""
        # Add to internal listeners
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

        # Add to WebSocket if available
        if self._websocket:
            self._websocket.add_listener(event, callback)

    def remove_event_listener(self, event: str, callback: Callable) -> None:
        """Remove event listener"""
        # Remove from internal listeners
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)

        # Remove from WebSocket if available
        if self._websocket:
            self._websocket.remove_listener(event, callback)

    @property
    def websocket_info(self) -> dict[str, Any]:
        """Get WebSocket connection information"""
        if self._websocket:
            return self._websocket.connection_info
        return {
            "connected": False,
            "enabled": settings.WEBSOCKET_ENABLED,
            "websocket_instance": None,
        }

    # ==================== LIFECYCLE METHODS ====================

    async def start(self, *, connect_websocket: bool | None = None) -> None:
        """Start the client and connect to WebSocket if requested"""
        if self._closed:
            msg = "Cannot start a closed client"
            raise RuntimeError(msg)

        try:
            # Use settings default if not specified
            if connect_websocket is None:
                connect_websocket = settings.WEBSOCKET_ENABLED

            # Initialize and connect WebSocket if requested
            if connect_websocket:
                if self._websocket is None:
                    self._websocket = WebSocketClient(self)
                await self._websocket.connect()

                # Initialize deferred WebSocket listeners
                await self.events.initialize_deferred_websockets()

            self._ready = True
            logger.info("UAProjectClient is ready")

        except Exception as e:
            logger.exception(f"Client startup failed: {e}")
            raise

    async def close(self) -> None:
        """Close the client and cleanup resources"""
        if self._closed:
            return

        self._closed = True
        self._ready = False

        # Close WebSocket connection
        if self._websocket:
            await self._websocket.disconnect()

        # Close HTTP client
        if self._http_client:
            await self._http_client.close()

        logger.info("UAProjectClient closed")

    # Context manager support
    async def __aenter__(self) -> "UAProjectClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    # Utility methods
    def is_ready(self) -> bool:
        """Check if client is ready"""
        return self._ready and not self._closed

    def is_closed(self) -> bool:
        """Check if client is closed"""
        return self._closed

    @property
    def is_impersonating(self) -> bool:
        """Check if client is currently impersonating a user"""
        return self.impersonate_user_id is not None

    def impersonate(self, user_id: int) -> "UAProjectClient":
        """Create new client that impersonates a specific user"""
        return UAProjectClient(
            api_key=self.api_key,
            base_url=self.base_url,
            impersonate_user_id=user_id,
        )

    def impersonate_discord(self, discord_id: int) -> "UAProjectClient":
        """Create new client that impersonates a user by Discord ID"""
        return UAProjectClient(
            api_key=self.api_key,
            base_url=self.base_url,
            impersonate_discord_id=discord_id,
        )
    
    @classmethod
    def with_impersonation(cls, *, discord_id: int | None = None, user_id: int | None = None, **kwargs) -> "UAProjectClient":
        """Create client with impersonation (either Discord ID or user ID)"""
        if discord_id is not None and user_id is not None:
            raise ValueError("Cannot specify both discord_id and user_id")
        if discord_id is None and user_id is None:
            raise ValueError("Must specify either discord_id or user_id")
        
        if discord_id is not None:
            return cls(impersonate_discord_id=discord_id, **kwargs)
        else:
            return cls(impersonate_user_id=user_id, **kwargs)

    def discord_integration(self):
        """Create Discord integration for this client"""
        from awesome_backend_client.integrations.discord import DiscordIntegration
        return DiscordIntegration(self)

    class ImpersonationContext:
        """Context manager for temporary user impersonation"""

        def __init__(self, client: "UAProjectClient", user_id: int) -> None:
            self.client = client
            self.user_id = user_id
            self.original_user_id: int | None = None

        async def __aenter__(self) -> "UAProjectClient.ImpersonationContext":
            self.original_user_id = self.client.impersonate_user_id
            self.client.impersonate_user_id = self.user_id
            if self.client._http_client:
                self.client._http_client.set_impersonation(self.user_id)
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            self.client.impersonate_user_id = self.original_user_id
            if self.client._http_client:
                self.client._http_client.set_impersonation(self.original_user_id)

    def impersonate_context(self, user_id: int) -> ImpersonationContext:
        """Context manager for temporary impersonation"""
        return self.ImpersonationContext(self, user_id)

    def __repr__(self) -> str:
        mode = (
            f"impersonating user {self.impersonate_user_id}"
            if self.is_impersonating
            else "bot mode"
        )
        return f"<UAProjectClient {mode}>"
