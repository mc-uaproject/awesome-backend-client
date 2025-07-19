"""
Advanced webhook management system for UAProject

Provides automatic webhook registration, HMAC signature validation,
event-driven payload customization, and comprehensive webhook lifecycle management.
"""

import asyncio
import hashlib
import hmac
import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel
from uaproject_backend_schemas.models.schemas.webhook import (
    ConditionOperator,
    WebhookAuthType,
    WebhookCondition,
    WebhookConditionGroup,
    WebhookEvent,
    WebhookFieldMapping,
    WebhookRetryPolicy,
    WebhookTrigger,
)
from uaproject_backend_schemas.models.webhook import Webhook as WebhookConfig

from .core.config import settings

logger = logging.getLogger(__name__)


class WebhookAuthConfig(BaseModel):
    auth_type: WebhookAuthType
    secret_key: str | None = None
    token: str | None = None
    username: str | None = None
    password: str | None = None


class WebhookTemplate:
    """Predefined webhook templates for common use cases"""

    @staticmethod
    def user_events(endpoint: str, secret_key: str | None = None) -> WebhookConfig:
        """Template for user-related events"""
        return WebhookConfig(
            name="User Events Webhook",
            description="Webhook for all user-related events",
            endpoint=endpoint,
            triggers=[
                WebhookTrigger(
                    model_name="User",
                    events=[
                        WebhookEvent.CREATE,
                        WebhookEvent.UPDATE,
                        WebhookEvent.DELETE,
                    ],
                    fields=[
                        WebhookFieldMapping(source_path="id", target_field="user_id"),
                        WebhookFieldMapping(
                            source_path="discord_id", target_field="discord_id"
                        ),
                        WebhookFieldMapping(
                            source_path="minecraft_nickname", target_field="nickname"
                        ),
                        WebhookFieldMapping(
                            source_path="status", target_field="status"
                        ),
                    ],
                )
            ],
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.HMAC,
                secret_key=secret_key or settings.WEBHOOK_SECRET,
            )
            if secret_key or settings.WEBHOOK_SECRET
            else None,
            retry_policy=WebhookRetryPolicy(),
        )

    @staticmethod
    def application_events(
        endpoint: str, secret_key: str | None = None
    ) -> WebhookConfig:
        """Template for application-related events"""
        return WebhookConfig(
            name="Application Events Webhook",
            description="Webhook for application status changes",
            endpoint=endpoint,
            triggers=[
                WebhookTrigger(
                    model_name="Application",
                    events=[WebhookEvent.CREATE, WebhookEvent.UPDATE],
                    conditions=WebhookConditionGroup(
                        operator="OR",
                        conditions=[
                            WebhookCondition(
                                field="status",
                                operator=ConditionOperator.CHANGED,
                                value=None,
                            ),
                            WebhookCondition(
                                field="result",
                                operator=ConditionOperator.CHANGED,
                                value=None,
                            ),
                        ],
                    ),
                )
            ],
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.HMAC,
                secret_key=secret_key or settings.WEBHOOK_SECRET,
            )
            if secret_key or settings.WEBHOOK_SECRET
            else None,
            retry_policy=WebhookRetryPolicy(),
        )

    @staticmethod
    def transaction_events(
        endpoint: str, secret_key: str | None = None
    ) -> WebhookConfig:
        """Template for transaction-related events"""
        return WebhookConfig(
            name="Transaction Events Webhook",
            description="Webhook for financial transactions",
            endpoint=endpoint,
            triggers=[
                WebhookTrigger(
                    model_name="Transaction",
                    events=[WebhookEvent.CREATE],
                    conditions=WebhookConditionGroup(
                        operator="AND",
                        conditions=[
                            WebhookCondition(
                                field="amount", operator=ConditionOperator.GT, value=0
                            ),
                            WebhookCondition(
                                field="status",
                                operator=ConditionOperator.EQ,
                                value="completed",
                            ),
                        ],
                    ),
                )
            ],
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.HMAC,
                secret_key=secret_key or settings.WEBHOOK_SECRET,
            )
            if secret_key or settings.WEBHOOK_SECRET
            else None,
            retry_policy=WebhookRetryPolicy(),
        )


class WebhookSignatureValidator:
    """HMAC signature validation for webhooks"""

    @staticmethod
    def generate_signature(payload: str, secret: str, algorithm: str = "sha256") -> str:
        """Generate HMAC signature for webhook payload"""
        key = secret.encode("utf-8")
        message = payload.encode("utf-8")
        signature = hmac.new(key, message, getattr(hashlib, algorithm)).hexdigest()
        return f"{algorithm}={signature}"

    @staticmethod
    def verify_signature(
        payload: str, signature: str, secret: str, algorithm: str = "sha256"
    ) -> bool:
        """Verify webhook payload signature"""
        expected_signature = WebhookSignatureValidator.generate_signature(
            payload, secret, algorithm
        )
        return hmac.compare_digest(signature, expected_signature)

    @staticmethod
    def extract_signature(signature_header: str) -> tuple[str, str]:
        """Extract algorithm and signature from header"""
        try:
            algorithm, signature = signature_header.split("=", 1)
            return algorithm, signature
        except ValueError as e:
            raise ValueError(
                "Invalid signature format. Expected 'algorithm=signature'"
            ) from e


class WebhookRegistrar:
    """Automatic webhook registration and management"""

    def __init__(self, client):
        self.client = client
        self._registered_webhooks: dict[str, int] = {}
        self._event_handlers: dict[str, list[Callable]] = {}

    async def register_webhook(self, config: WebhookConfig) -> int | None:
        """Register a webhook with the backend"""
        try:
            webhook_data = {
                "name": config.name,
                "description": config.description,
                "endpoint": config.endpoint,
                "status": config.status.value,
                "triggers": [trigger.model_dump() for trigger in config.triggers],
            }

            # Add authentication configuration
            if config.auth_config:
                webhook_data["auth_type"] = config.auth_config.auth_type.value
                webhook_data["auth_config"] = self._prepare_auth_config(
                    config.auth_config
                )

            # Add retry policy
            if config.retry_policy:
                webhook_data["retry_policy"] = config.retry_policy.model_dump()

            # Add payload configuration
            if config.payload_config:
                webhook_data["payload_config"] = config.payload_config

            response = await self.client.webhooks.create(webhook_data)
            webhook_id = response["id"]

            self._registered_webhooks[config.name] = webhook_id
            logger.info(f"Registered webhook '{config.name}' with ID {webhook_id}")

            return webhook_id

        except Exception as e:
            logger.error(f"Failed to register webhook '{config.name}': {e}")
            return None

    def _prepare_auth_config(self, auth_config: WebhookAuthConfig) -> dict[str, Any]:
        """Prepare auth config for API request"""
        config_data = {}

        if auth_config.auth_type == WebhookAuthType.BEARER and auth_config.token:
            config_data["token"] = auth_config.token
        elif auth_config.auth_type == WebhookAuthType.BASIC:
            if auth_config.username and auth_config.password:
                config_data["username"] = auth_config.username
                config_data["password"] = auth_config.password
        elif auth_config.auth_type == WebhookAuthType.API_KEY:
            if auth_config.api_key_header and auth_config.api_key_value:
                config_data["header"] = auth_config.api_key_header
                config_data["value"] = auth_config.api_key_value
        elif auth_config.auth_type == WebhookAuthType.HMAC and auth_config.secret_key:
            config_data["secret_key"] = auth_config.secret_key
        elif (
            auth_config.auth_type == WebhookAuthType.CUSTOM
            and auth_config.custom_headers
        ):
            config_data["headers"] = auth_config.custom_headers

        return config_data

    async def unregister_webhook(self, name: str) -> bool:
        """Unregister a webhook by name"""
        if name not in self._registered_webhooks:
            logger.warning(f"Webhook '{name}' not found in registered webhooks")
            return False

        webhook_id = self._registered_webhooks[name]
        try:
            await self.client.webhooks.delete(webhook_id)
            del self._registered_webhooks[name]
            logger.info(f"Unregistered webhook '{name}' (ID: {webhook_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister webhook '{name}': {e}")
            return False

    async def register_template(
        self, template_name: str, endpoint: str, **kwargs
    ) -> int | None:
        """Register a predefined webhook template"""
        templates = {
            "user_events": WebhookTemplate.user_events,
            "application_events": WebhookTemplate.application_events,
            "transaction_events": WebhookTemplate.transaction_events,
        }

        if template_name not in templates:
            logger.error(f"Unknown webhook template: {template_name}")
            return None

        config = templates[template_name](endpoint, **kwargs)
        return await self.register_webhook(config)

    async def auto_register_common_webhooks(
        self, base_endpoint: str
    ) -> dict[str, int | None]:
        """Automatically register common webhook templates"""
        if not settings.WEBHOOK_AUTO_REGISTER:
            logger.info("Webhook auto-registration is disabled")
            return {}

        results = {}
        templates = ["user_events", "application_events", "transaction_events"]

        for template_name in templates:
            endpoint = f"{base_endpoint.rstrip('/')}/{template_name}"
            webhook_id = await self.register_template(template_name, endpoint)
            results[template_name] = webhook_id

        return results

    async def get_webhook_logs(
        self,
        webhook_id: int | None = None,
        limit: int = 100,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get webhook execution logs"""
        params = {"limit": limit}
        if webhook_id:
            params["webhook_id"] = webhook_id
        if status:
            params["status"] = status

        return await self.client.webhook_logs.list(**params)

    def add_event_handler(self, event_pattern: str, handler: Callable):
        """Add event handler for webhook events"""
        if event_pattern not in self._event_handlers:
            self._event_handlers[event_pattern] = []
        self._event_handlers[event_pattern].append(handler)

    async def _execute_handlers(self, pattern: str, payload: dict[str, Any]):
        """Execute handlers for a specific event pattern"""
        if pattern in self._event_handlers:
            for handler in self._event_handlers[pattern]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(payload)
                    else:
                        handler(payload)
                except Exception as e:
                    logger.error(f"Error in webhook handler for {pattern}: {e}")

    async def handle_webhook_event(self, payload: dict[str, Any]):
        """Handle incoming webhook event"""
        event_type = payload.get("event")
        model = payload.get("model")

        if not event_type or not model:
            logger.warning("Invalid webhook payload: missing event or model")
            return

        # Try specific handler first
        specific_pattern = f"{model}.{event_type}"
        await self._execute_handlers(specific_pattern, payload)

        # Try general handlers
        general_patterns = [f"{model}.*", f"*.{event_type}", "*.*"]
        for pattern in general_patterns:
            await self._execute_handlers(pattern, payload)

    @property
    def registered_webhooks(self) -> dict[str, int]:
        """Get list of registered webhooks"""
        return self._registered_webhooks.copy()


class WebhookEventDecorator:
    """Decorator for webhook event handlers"""

    def __init__(self, registrar: WebhookRegistrar):
        self.registrar = registrar

    def on_webhook(self, event_pattern: str):
        """Decorator for webhook event handlers

        Examples:
            @webhook_events.on_webhook("User.create")
            async def handle_user_create(payload):
                print(f"New user created: {payload['data']['id']}")

            @webhook_events.on_webhook("Application.*")
            async def handle_application_events(payload):
                print(f"Application event: {payload['event']}")
        """

        def decorator(func):
            self.registrar.add_event_handler(event_pattern, func)
            return func

        return decorator


# Export main classes and functions
__all__ = [
    "WebhookAuthConfig",
    "WebhookAuthType",
    "WebhookConfig",
    "WebhookEvent",
    "WebhookEventDecorator",
    "WebhookRegistrar",
    "WebhookSignatureValidator",
    "WebhookTemplate",
    "WebhookTrigger",
]
