"""Webhook model with methods for webhook operations"""

import logging
from typing import TYPE_CHECKING

from uaproject_backend_schemas.models import (
    Webhook as WebhookSchema,
)

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.webhook import WebhookSchemaResponse

    from awesome_backend_client.client import UAProjectClient
else:
    WebhookSchemaResponse = WebhookSchema.schemas.response

logger = logging.getLogger(__name__)


class Webhook(BaseBackendModel, WebhookSchemaResponse):
    """
    Webhook model with methods for webhook operations
    """

    def __init__(
        self, webhook_schema: WebhookSchemaResponse, *, client: "UAProjectClient"
    ):
        super().__init__(webhook_schema, client=client)

    async def refresh(self):
        """Refresh webhook data from API"""
        try:
            fresh_data = await self._client.webhooks.get(self.id)
            self._schema = WebhookSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh webhook {self.id}: {e}")

    async def edit(self, **fields) -> "Webhook":
        """Edit webhook fields"""
        updated_data = await self._client.webhooks.update(self.id, fields)
        self._schema = WebhookSchema.model_validate(updated_data)
        return self

    async def update_events(self, events: list[str]) -> "Webhook":
        """Update webhook events"""
        return await self.edit(events=events)

    async def activate(self) -> "Webhook":
        """Activate webhook"""
        return await self.edit(is_active=True)

    async def deactivate(self) -> "Webhook":
        """Deactivate webhook"""
        return await self.edit(is_active=False)

    async def delete(self) -> bool:
        """Delete this webhook"""
        return await self._client.webhooks.delete(self.id)

    def __str__(self) -> str:
        return f"Webhook(id={self.id}, url='{self.url}')"

    def __repr__(self) -> str:
        return f"<Webhook id={self.id} url='{self.url}'>"
