"""
Universal event system for UAProject backend client.

Provides unified decorators and lazy registration for both WebSocket and Webhook events.
Events are only registered when explicitly requested through decorators or manual
registration.
"""

import asyncio
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .core.config import settings
from .payload import EventPayload, create_payload

logger = logging.getLogger(__name__)


class EventSource(str, Enum):
    """Event source types"""

    WEBSOCKET = "websocket"
    WEBHOOK = "webhook"
    BOTH = "both"  # Listen to both WebSocket and Webhook events


class EventTrigger(BaseModel):
    """Event trigger configuration"""

    model: str = Field(..., description="Model name (User, Application, etc.)")
    action: str = Field(..., description="Action (create, update, delete, etc.)")
    conditions: dict[str, Any] | None = Field(
        None, description="Conditions for triggering"
    )
    fields: list[str] | None = Field(
        None, description="Specific fields to watch for changes"
    )


class EventConfig(BaseModel):
    """Event configuration"""

    source: EventSource = Field(EventSource.BOTH, description="Event source")
    triggers: list[EventTrigger] = Field(..., description="Event triggers")
    webhook_config: dict[str, Any] | None = Field(
        None, description="Webhook-specific configuration"
    )
    websocket_config: dict[str, Any] | None = Field(
        None, description="WebSocket-specific configuration"
    )
    priority: int = Field(0, description="Event priority (higher = first)")
    debounce_ms: int | None = Field(None, description="Debounce delay in milliseconds")
    rate_limit: int | None = Field(None, description="Max events per second")


class EventHandler:
    """Event handler wrapper"""

    def __init__(self, handler: Callable, config: EventConfig, pattern: str):
        self.handler = handler
        self.config = config
        self.pattern = pattern
        self.call_count = 0
        self.last_called = None
        self._rate_limiter = {}

    async def __call__(self, payload: EventPayload) -> Any:
        """Execute the event handler with rate limiting and debouncing"""
        import time

        current_time = time.time()

        # Rate limiting
        if self.config.rate_limit:
            if self.pattern not in self._rate_limiter:
                self._rate_limiter[self.pattern] = []

            # Clean old entries
            cutoff = current_time - 1.0  # 1 second window
            self._rate_limiter[self.pattern] = [
                t for t in self._rate_limiter[self.pattern] if t > cutoff
            ]

            if len(self._rate_limiter[self.pattern]) >= self.config.rate_limit:
                logger.warning(f"Rate limit exceeded for event {self.pattern}")
                return None

            self._rate_limiter[self.pattern].append(current_time)

        # Debouncing
        if self.config.debounce_ms:
            if self.last_called:
                time_diff = (current_time - self.last_called) * 1000
                if time_diff < self.config.debounce_ms:
                    logger.debug(f"Event {self.pattern} debounced")
                    return None

        self.last_called = current_time
        self.call_count += 1

        try:
            if asyncio.iscoroutinefunction(self.handler):
                return await self.handler(payload)
            return self.handler(payload)
        except Exception as e:
            logger.error(f"Error in event handler {self.pattern}: {e}")


class UniversalEventManager:
    """Universal event manager for WebSocket and Webhook events"""

    def __init__(self, client):
        self.client = client
        self._handlers: dict[str, list[EventHandler]] = {}
        self._websocket_listeners: dict[str, list[Callable]] = {}
        self._webhook_registrations: dict[str, dict[str, Any]] = {}
        self._lazy_initialized = False

    def on(
        self,
        pattern: str,
        *,
        source: EventSource = EventSource.BOTH,
        model: str | None = None,
        action: str | None = None,
        conditions: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        webhook_config: dict[str, Any] | None = None,
        websocket_config: dict[str, Any] | None = None,
        priority: int = 0,
        debounce_ms: int | None = None,
        rate_limit: int | None = None,
    ):
        """
        Universal event decorator

        Args:
            pattern: Event pattern (e.g., "User.create", "Application.*", "*.*")
            source: Event source (websocket, webhook, or both)
            model: Model name (if not in pattern)
            action: Action name (if not in pattern)
            conditions: Conditions for triggering
            fields: Specific fields to watch
            webhook_config: Webhook-specific configuration
            websocket_config: WebSocket-specific configuration
            priority: Handler priority
            debounce_ms: Debounce delay
            rate_limit: Rate limiting

        Examples:
            @client.events.on("User.create")
            async def handle_user_create(payload):
                print(f"New user: {payload['data']['id']}")

            @client.events.on(
                "User.update",
                fields=["status", "minecraft_nickname"],
                conditions={"status": "active"},
                debounce_ms=1000
            )
            async def handle_user_update(payload):
                print(f"User updated: {payload}")

            @client.events.on(
                "Application.*",
                source=EventSource.WEBHOOK,
                webhook_config={"secret_key": "custom-secret"}
            )
            async def handle_app_events(payload):
                print(f"Application event: {payload}")
        """

        def decorator(func):
            # Parse pattern
            if "." in pattern:
                pattern_model, pattern_action = pattern.split(".", 1)
            else:
                pattern_model = model or "*"
                pattern_action = action or "*"

            # Create triggers
            triggers = []
            if pattern_model != "*" or pattern_action != "*":
                triggers.append(
                    EventTrigger(
                        model=pattern_model,
                        action=pattern_action,
                        conditions=conditions,
                        fields=fields,
                    )
                )

            # Create event config
            config = EventConfig(
                source=source,
                triggers=triggers,
                webhook_config=webhook_config or {},
                websocket_config=websocket_config or {},
                priority=priority,
                debounce_ms=debounce_ms,
                rate_limit=rate_limit,
            )

            # Create handler
            handler = EventHandler(func, config, pattern)

            # Register handler
            self._register_handler(pattern, handler)

            return func

        return decorator

    def _register_handler(self, pattern: str, handler: EventHandler):
        """Register an event handler"""
        if pattern not in self._handlers:
            self._handlers[pattern] = []

        # Insert handler based on priority
        inserted = False
        for i, existing_handler in enumerate(self._handlers[pattern]):
            if handler.config.priority > existing_handler.config.priority:
                self._handlers[pattern].insert(i, handler)
                inserted = True
                break

        if not inserted:
            self._handlers[pattern].append(handler)

        logger.debug(f"Registered handler for pattern: {pattern}")

        # Lazy initialization of listeners
        self._ensure_listeners_registered(pattern, handler.config)

    def _ensure_listeners_registered(self, pattern: str, config: EventConfig):
        """Ensure WebSocket and Webhook listeners are registered"""
        # Register WebSocket listeners
        if config.source in (EventSource.WEBSOCKET, EventSource.BOTH):
            self._register_websocket_listener(pattern, config)

        # Register Webhook listeners
        if config.source in (EventSource.WEBHOOK, EventSource.BOTH):
            self._register_webhook_listener(pattern, config)

    def _register_websocket_listener(self, pattern: str, config: EventConfig):
        """Register WebSocket listener for pattern"""
        if not self.client._websocket:
            # WebSocket will be registered when connection is established
            logger.debug(
                f"WebSocket not available, deferring registration for {pattern}"
            )
            return

        if pattern not in self._websocket_listeners:
            self._websocket_listeners[pattern] = []

        async def websocket_handler(data):
            """Handle WebSocket event"""
            # Build payload from WebSocket data
            payload = self._build_websocket_payload(data, pattern, config)
            await self._handle_event(pattern, payload)

        # Add to WebSocket client
        self.client._websocket.add_listener(pattern, websocket_handler)
        self._websocket_listeners[pattern].append(websocket_handler)

        logger.debug(f"Registered WebSocket listener for: {pattern}")

    def _register_webhook_listener(self, pattern: str, config: EventConfig):
        """Register Webhook listener for pattern"""
        if pattern in self._webhook_registrations:
            logger.debug(f"Webhook already registered for pattern: {pattern}")
            return

        # Only create webhook registration metadata, actual webhook creation is lazy
        webhook_data = {"pattern": pattern, "config": config, "registered": False}

        self._webhook_registrations[pattern] = webhook_data
        logger.debug(f"Prepared webhook registration for: {pattern}")

    async def _ensure_webhook_registered(self, pattern: str):
        """Ensure webhook is actually registered when needed"""
        if pattern not in self._webhook_registrations:
            return False

        webhook_data = self._webhook_registrations[pattern]
        if webhook_data["registered"]:
            return True

        config = webhook_data["config"]

        # Create webhook only when first event handler is registered
        if settings.WEBHOOK_AUTO_REGISTER and settings.WEBHOOK_ENDPOINT_URL:
            from .webhooks import (
                WebhookAuthConfig,
                WebhookAuthType,
                WebhookConfig,
                WebhookTrigger,
            )

            # Build webhook config from event config
            triggers = []
            for trigger in config.triggers:
                webhook_trigger = WebhookTrigger(
                    model_name=trigger.model,
                    events=[trigger.action]
                    if trigger.action != "*"
                    else ["create", "update", "delete"],
                    conditions=trigger.conditions,
                    fields=trigger.fields,
                )
                triggers.append(webhook_trigger)

            webhook_config = WebhookConfig(
                name=f"Auto Event Webhook - {pattern}",
                description=(
                    f"Automatically created webhook for event pattern: {pattern}"
                ),
                endpoint=f"{settings.WEBHOOK_ENDPOINT_URL}/{pattern.replace('.', '/')}",
                triggers=triggers,
                auth_config=WebhookAuthConfig(
                    auth_type=WebhookAuthType.HMAC, secret_key=settings.WEBHOOK_SECRET
                )
                if settings.WEBHOOK_SECRET
                else None,
                **config.webhook_config,
            )

            # Register webhook
            webhook_id = await self.client.webhook_registrar.register_webhook(
                webhook_config
            )
            if webhook_id:
                webhook_data["registered"] = True
                webhook_data["webhook_id"] = webhook_id
                logger.info(f"Registered webhook {webhook_id} for pattern: {pattern}")
                return True
            logger.error(f"Failed to register webhook for pattern: {pattern}")
            return False

        return False

    def _build_websocket_payload(
        self, data: Any, pattern: str, config: EventConfig
    ) -> EventPayload:
        """Build payload from WebSocket data"""
        # Default payload structure
        payload_data = {
            "source": "websocket",
            "pattern": pattern,
            "data": data,
            "timestamp": self._get_current_timestamp(),
        }

        # Apply WebSocket-specific configuration
        if config.websocket_config:
            # Custom payload transformation
            if "payload_transform" in config.websocket_config:
                transform_func = config.websocket_config["payload_transform"]
                if callable(transform_func):
                    payload_data = transform_func(payload_data, data)

            # Add custom fields
            if "custom_fields" in config.websocket_config:
                payload_data.update(config.websocket_config["custom_fields"])

        return create_payload(payload_data, "websocket")

    async def _handle_event(self, pattern: str, payload: EventPayload):
        """Handle event with all matching handlers"""
        matching_patterns = self._get_matching_patterns(pattern, payload)

        for match_pattern in matching_patterns:
            if match_pattern in self._handlers:
                for handler in self._handlers[match_pattern]:
                    try:
                        await handler(payload)
                    except Exception as e:
                        logger.error(f"Error in event handler {match_pattern}: {e}")

    def _get_matching_patterns(self, pattern: str, payload: EventPayload) -> list[str]:
        """Get all patterns that match the event"""
        matching = []

        # Extract model and action from payload or pattern
        if "." in pattern:
            model, action = pattern.split(".", 1)
        else:
            model = payload.get("model", "*")
            action = payload.get("event", payload.get("action", "*"))

        # Check all registered patterns
        for registered_pattern in self._handlers.keys():
            if self._pattern_matches(registered_pattern, model, action):
                matching.append(registered_pattern)

        return matching

    def _pattern_matches(self, pattern: str, model: str, action: str) -> bool:
        """Check if pattern matches model.action"""
        if "." in pattern:
            pattern_model, pattern_action = pattern.split(".", 1)
        else:
            return True  # Invalid pattern matches everything

        # Check model match
        model_match = (
            pattern_model == "*"
            or pattern_model == model
            or pattern_model.lower() == model.lower()
        )

        # Check action match
        action_match = (
            pattern_action == "*"
            or pattern_action == action
            or pattern_action.lower() == action.lower()
        )

        return model_match and action_match

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    async def handle_webhook_payload(self, payload_data: dict[str, Any]):
        """Handle incoming webhook payload"""
        # Ensure webhook is registered for this payload
        event = payload_data.get("event", "")
        model = payload_data.get("model", "")
        pattern = f"{model}.{event}"

        # Add source info to payload data
        payload_data["source"] = "webhook"

        # Create EventPayload object
        payload = create_payload(payload_data, "webhook")

        await self._handle_event(pattern, payload)

    async def initialize_deferred_websockets(self):
        """Initialize WebSocket listeners that were deferred"""
        if not self.client._websocket:
            return

        for pattern, handlers in self._handlers.items():
            for handler in handlers:
                if handler.config.source in (EventSource.WEBSOCKET, EventSource.BOTH):
                    if pattern not in self._websocket_listeners:
                        self._register_websocket_listener(pattern, handler.config)

    def list_handlers(self) -> dict[str, list[str]]:
        """List all registered event handlers"""
        result = {}
        for pattern, handlers in self._handlers.items():
            result[pattern] = [
                f"{handler.handler.__name__} (priority: {handler.config.priority}, "
                f"source: {handler.config.source.value})"
                for handler in handlers
            ]
        return result

    def get_stats(self) -> dict[str, Any]:
        """Get event system statistics"""
        return {
            "total_handlers": sum(
                len(handlers) for handlers in self._handlers.values()
            ),
            "patterns": list(self._handlers.keys()),
            "websocket_listeners": len(self._websocket_listeners),
            "webhook_registrations": len(self._webhook_registrations),
            "registered_webhooks": len(
                [
                    w
                    for w in self._webhook_registrations.values()
                    if w.get("registered", False)
                ]
            ),
        }


# For backward compatibility, keep the old decorators as aliases
class BackwardCompatibilityDecorators:
    """Backward compatibility decorators"""

    def __init__(self, event_manager: UniversalEventManager):
        self.event_manager = event_manager

    def event(self, func):
        """Legacy @client.event decorator"""
        event_name = func.__name__
        event_name = event_name.removeprefix("on_")  # Remove 'on_' prefix

        return self.event_manager.on(event_name)(func)

    def listen(self, name: str | None = None):
        """Legacy @client.listen decorator"""

        def decorator(func):
            event_name = name or func.__name__
            return self.event_manager.on(event_name)(func)

        return decorator

    def on_webhook(self, pattern: str):
        """Legacy webhook decorator"""
        return self.event_manager.on(pattern, source=EventSource.WEBHOOK)


# Export main classes
__all__ = [
    "BackwardCompatibilityDecorators",
    "EventConfig",
    "EventHandler",
    "EventSource",
    "EventTrigger",
    "UniversalEventManager",
]
