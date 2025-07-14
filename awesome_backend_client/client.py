"""
UAProject Backend Client - disnake style

Simple and clean API client for UAProject backend.
Uses existing backend patterns and schemas without duplication.
"""

import logging
from typing import Any, Callable, Optional, Union

from uaproject_backend_schemas.models import (
    Application,
    Balance,
    Punishment,
    Service,
    Transaction,
    User,
)

from .core.config import settings
from .events import BackwardCompatibilityDecorators, UniversalEventManager
from .http import HTTPClient
from .managers import (
    ApplicationManager,
    ApplicationSectionManager,
    BalanceManager,
    DebugManager,
    FileManager,
    PunishmentManager,
    RoleManager,
    ServiceManager,
    TransactionManager,
    UserManager,
    WebhookLogManager,
    WebhookManager,
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
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        impersonate_user_id: Optional[int] = None,
    ):
        """Initialize UAProject client"""
        self.api_key = api_key or settings.BACKEND_API_KEY
        self.base_url = base_url or settings.FULL_API_URL
        self.impersonate_user_id = impersonate_user_id

        # Internal state
        self._ready = False
        self._closed = False
        self._http_client: Optional[HTTPClient] = None
        self._websocket: Optional[WebSocketClient] = None

        # Universal Event System (NEW)
        self.events = UniversalEventManager(self)
        self._legacy_decorators = BackwardCompatibilityDecorators(self.events)

        # Legacy event system (for backward compatibility)
        self._listeners: dict[str, list[Callable]] = {}

        # Webhook system
        self.webhook_registrar = WebhookRegistrar(self)

        # Resource managers (discord.py style) - Universal CRUD for all resources
        self.users = UserManager(self)
        self.roles = RoleManager(self)
        self.applications = ApplicationManager(self)
        self.application_sections = ApplicationSectionManager(self)
        self.balances = BalanceManager(self)
        self.transactions = TransactionManager(self)
        self.punishments = PunishmentManager(self)
        self.services = ServiceManager(self)
        self.files = FileManager(self)
        self.webhooks = WebhookManager(self)
        self.webhook_logs = WebhookLogManager(self)
        self.debug = DebugManager(self)

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
            )
        return self._http_client

    # ==================== HTTP REQUEST METHODS ====================

    async def _request(
        self, method: str, endpoint: str, **kwargs
    ) -> Union[dict[str, Any], list[dict[str, Any]]]:
        """Make HTTP request with error handling"""
        if method == "GET":
            return await self.http.get(endpoint, **kwargs)
        elif method == "POST":
            return await self.http.post(endpoint, **kwargs)
        elif method == "PUT":
            return await self.http.put(endpoint, **kwargs)
        elif method == "PATCH":
            return await self.http.patch(endpoint, **kwargs)
        elif method == "DELETE":
            return await self.http.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    # ==================== USER METHODS (discord.py style) ====================

    async def fetch_user(self, user_id: int) -> Optional[User]:
        """Fetch user by ID (always from API, like discord.py fetch_user)"""
        try:
            data = await self.users.get(user_id)
            return User.model_validate(data)
        except Exception:
            return None

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID (same as fetch_user since caching disabled)"""
        return await self.fetch_user(user_id)

    @property
    def user(self):
        """Current user manager (like discord.py client.user)"""
        return self.users

    async def fetch_users(self, *, limit: int = 50, **filters) -> list[User]:
        """Fetch multiple users"""
        try:
            data = await self.users.list(limit=limit, **filters)
            return [User.model_validate(user) for user in data]
        except Exception:
            return []

    async def search_users(self, nickname: str, *, limit: int = 10) -> list[User]:
        """Search users by nickname"""
        try:
            data = await self.users.search_by_nickname(nickname, limit=limit)
            return [User.model_validate(user) for user in data]
        except Exception:
            return []

    # ==================== APPLICATION METHODS ====================

    async def fetch_application(self, app_id: int) -> Optional[Application]:
        """Fetch application by ID"""
        try:
            data = await self.applications.get(app_id)
            return Application.model_validate(data)
        except Exception:
            return None

    async def fetch_applications(
        self, *, limit: int = 50, **filters
    ) -> list[Application]:
        """Fetch multiple applications"""
        try:
            data = await self.applications.list(limit=limit, **filters)
            return [Application.model_validate(app) for app in data]
        except Exception:
            return []

    # ==================== BALANCE METHODS ====================

    async def fetch_balance(self, balance_id: int) -> Optional[Balance]:
        """Fetch balance by ID"""
        try:
            data = await self.balances.get(balance_id)
            return Balance.model_validate(data)
        except Exception:
            return None

    async def fetch_user_balance(self, user_id: int) -> Optional[Balance]:
        """Fetch specific user's balance"""
        try:
            data = await self.balances.list(user_id=user_id, limit=1)
            if data:
                return Balance.model_validate(data[0])
        except Exception:
            pass
        return None

    # ==================== TRANSACTION METHODS ====================

    async def fetch_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Fetch transaction by ID"""
        try:
            data = await self.transactions.get(transaction_id)
            return Transaction.model_validate(data)
        except Exception:
            return None

    async def fetch_transactions(
        self, *, limit: int = 50, **filters
    ) -> list[Transaction]:
        """Fetch multiple transactions"""
        try:
            data = await self.transactions.list(limit=limit, **filters)
            return [Transaction.model_validate(tx) for tx in data]
        except Exception:
            return []

    # ==================== PUNISHMENT METHODS ====================

    async def fetch_punishment(self, punishment_id: int) -> Optional[Punishment]:
        """Fetch punishment by ID"""
        try:
            data = await self.punishments.get(punishment_id)
            return Punishment.model_validate(data)
        except Exception:
            return None

    # ==================== SERVICE METHODS ====================

    async def fetch_service(self, service_id: int) -> Optional[Service]:
        """Fetch service by ID"""
        try:
            data = await self.services.get(service_id)
            return Service.model_validate(data)
        except Exception:
            return None

    # ==================== CREATE/UPDATE METHODS ====================

    async def create_application(self, **app_data) -> Optional[Application]:
        """Create a new application"""
        try:
            data = await self.applications.create(app_data)
            return Application.model_validate(data)
        except Exception:
            return None

    async def update_user(
        self, user_id: Union[int, str], **user_data
    ) -> Optional[User]:
        """Update user data. Use 'me' for current user"""
        try:
            data = await self.users.update(user_id, user_data)
            return User.model_validate(data)
        except Exception:
            return None

    async def update_me(self, **user_data) -> Optional[User]:
        """Update current user data"""
        return await self.update_user("me", **user_data)

    # ==================== EVENT SYSTEM ====================

    def event(self, coro):
        """
        Legacy decorator for event handlers (discord.py style)

        Note: Use @client.events.on() for new code with more features

        Example:
            @client.event
            async def on_user_create(user):
                print(f"New user created: {user.minecraft_nickname}")
        """
        return self._legacy_decorators.event(coro)

    def listen(self, name: Optional[str] = None):
        """
        Legacy decorator for event listeners with custom event names

        Note: Use @client.events.on() for new code with more features

        Example:
            @client.listen('user_create')
            async def handle_new_user(user):
                print(f"New user: {user.minecraft_nickname}")
        """
        return self._legacy_decorators.listen(name)

    # ==================== WEBHOOK METHODS ====================

    async def register_webhook_template(
        self, template_name: str, endpoint: str, **kwargs
    ):
        """Register a predefined webhook template"""
        return await self.webhook_registrar.register_template(
            template_name, endpoint, **kwargs
        )

    async def auto_register_webhooks(self, base_endpoint: str):
        """Automatically register common webhooks"""
        return await self.webhook_registrar.auto_register_common_webhooks(base_endpoint)

    async def unregister_webhook(self, name: str):
        """Unregister a webhook by name"""
        return await self.webhook_registrar.unregister_webhook(name)

    @property
    def registered_webhooks(self):
        """Get registered webhooks"""
        return self.webhook_registrar.registered_webhooks

    async def handle_webhook_payload(self, payload: dict[str, Any]):
        """Handle incoming webhook payload"""
        return await self.events.handle_webhook_payload(payload)

    def list_event_handlers(self):
        """List all registered event handlers"""
        return self.events.list_handlers()

    def get_event_stats(self):
        """Get event system statistics"""
        return self.events.get_stats()

    # ==================== WEBSOCKET METHODS ====================

    @property
    def websocket(self) -> Optional[WebSocketClient]:
        """Get WebSocket client instance"""
        return self._websocket

    async def subscribe_events(self, events: list[str]) -> bool:
        """Subscribe to WebSocket events"""
        if self._websocket and self._websocket.is_connected:
            return await self._websocket.subscribe_events(events)
        return False

    async def unsubscribe_events(self, events: list[str]) -> bool:
        """Unsubscribe from WebSocket events"""
        if self._websocket and self._websocket.is_connected:
            return await self._websocket.unsubscribe_events(events)
        return False

    def add_event_listener(self, event: str, callback: Callable):
        """Add event listener for WebSocket events"""
        # Add to internal listeners
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

        # Add to WebSocket if available
        if self._websocket:
            self._websocket.add_listener(event, callback)

    def remove_event_listener(self, event: str, callback: Callable):
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

    async def start(self, *, connect_websocket: Optional[bool] = None):
        """Start the client and connect to WebSocket if requested"""
        if self._closed:
            raise RuntimeError("Cannot start a closed client")

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
            logger.error(f"Client startup failed: {e}")
            raise

    async def close(self):
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
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # noqa: U100
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

    class ImpersonationContext:
        """Context manager for temporary user impersonation"""

        def __init__(self, client: "UAProjectClient", user_id: int):
            self.client = client
            self.user_id = user_id
            self.original_user_id = None

        async def __aenter__(self):
            self.original_user_id = self.client.impersonate_user_id
            self.client.impersonate_user_id = self.user_id
            if self.client._http_client:
                self.client._http_client.set_impersonation(self.user_id)
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):  # noqa: U100
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
