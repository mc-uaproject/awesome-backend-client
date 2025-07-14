"""Advanced webhook resource manager with registration and management"""

from typing import TYPE_CHECKING, Any

from uaproject_backend_schemas.models.webhook import (
    Webhook as WebhookSchema,
)

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Webhook

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.webhook import (
        WebhookFilter,
        WebhookSchemaCreate,
        WebhookSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    from uaproject_backend_schemas.models.webhook import Webhook as WebhookSchema

    WebhookSchemaCreate = WebhookSchema.schemas.create
    WebhookSchemaUpdate = WebhookSchema.schemas.update
    WebhookFilter = WebhookSchema.filter


class WebhookManager(
    BaseCRUDManager[Webhook, WebhookSchemaCreate, WebhookSchemaUpdate, WebhookFilter]
):
    """Advanced webhook resource manager with registration and management"""

    def __init__(self, client: "UAProjectClient"):
        from awesome_backend_client.models import Webhook

        super().__init__(client, "webhooks", Webhook)

    async def create(self, data: dict[str, Any] | WebhookSchemaCreate) -> "Webhook":
        """Create new webhook"""
        return await super().create(data)

    async def update(
        self, item_id: int | str, data: dict[str, Any] | WebhookSchemaUpdate
    ) -> "Webhook":
        """Update webhook"""
        return await super().update(item_id, data)

    async def execute(self, webhook_id: int, data: dict[str, Any]) -> None:
        """Execute webhook manually"""
        await self.client.http.post(f"/webhooks/{webhook_id}/execute", data=data)

    async def test(self, webhook_id: int) -> dict[str, Any]:
        """Test webhook endpoint connectivity"""
        return await self.client.http.post(f"/webhooks/{webhook_id}/test")

    async def get_by_status(self, status: str) -> list["Webhook"]:
        """Get webhooks by status"""
        return await self.list(status=status)

    async def get_by_endpoint(self, endpoint: str) -> list["Webhook"]:
        """Get webhooks by endpoint URL"""
        return await self.list(endpoint=endpoint)

    async def activate(self, webhook_id: int) -> "Webhook":
        """Activate webhook"""
        return await self.update(webhook_id, {"status": "active"})

    async def deactivate(self, webhook_id: int) -> "Webhook":
        """Deactivate webhook"""
        return await self.update(webhook_id, {"status": "inactive"})

    async def pause(self, webhook_id: int) -> "Webhook":
        """Pause webhook"""
        return await self.update(webhook_id, {"status": "paused"})

    async def bulk_activate(self, webhook_ids: list[int]) -> list["Webhook"]:
        """Activate multiple webhooks"""
        results = []
        for webhook_id in webhook_ids:
            result = await self.activate(webhook_id)
            results.append(result)
        return results

    async def bulk_deactivate(self, webhook_ids: list[int]) -> list["Webhook"]:
        """Deactivate multiple webhooks"""
        results = []
        for webhook_id in webhook_ids:
            result = await self.deactivate(webhook_id)
            results.append(result)
        return results

    async def get_logs(
        self,
        webhook_id: int | None = None,
        limit: int = 100,
        status: str | None = None,
        **filters,
    ) -> list[dict[str, any]]:
        """Get webhook execution logs"""
        params = {"limit": limit, **filters}
        if webhook_id:
            params["webhook_id"] = webhook_id
        if status:
            params["status"] = status

        return await self.client.http.get("/webhook-logs", params=params)

    async def get_failed_logs(
        self, webhook_id: int | None = None, limit: int = 50
    ) -> list[dict[str, any]]:
        """Get failed webhook execution logs"""
        return await self.get_logs(webhook_id=webhook_id, status="failed", limit=limit)

    async def retry_failed(self, webhook_id: int, log_id: int) -> dict[str, any]:
        """Retry failed webhook execution"""
        return await self.client.http.post(f"/webhooks/{webhook_id}/retry/{log_id}")
