"""Webhook log model with methods for webhook log operations"""

import logging
from typing import TYPE_CHECKING

from uaproject_backend_schemas.models import (
    WebhookLog as WebhookLogSchema,
)

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.webhook_log import WebhookLogSchemaResponse

    from awesome_backend_client.client import UAProjectClient
else:
    WebhookLogSchemaResponse = WebhookLogSchema.schemas.response

logger = logging.getLogger(__name__)


class WebhookLog(BaseBackendModel, WebhookLogSchemaResponse):
    """
    Webhook log model with methods for webhook log operations
    """

    def __init__(
        self, webhook_log_schema: WebhookLogSchemaResponse, *, client: "UAProjectClient"
    ):
        super().__init__(webhook_log_schema, client=client)

    async def refresh(self):
        """Refresh webhook data from API"""
        try:
            fresh_data = await self._client.webhook_logs.get(self.id)
            self._schema = WebhookLogSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh webhook log {self.id}: {e}")

    async def edit(self, **fields) -> "WebhookLog":
        """Edit webhook log fields"""
        updated_data = await self._client.webhook_logs.update(self.id, fields)
        self._schema = WebhookLogSchema.model_validate(updated_data)
        return self
