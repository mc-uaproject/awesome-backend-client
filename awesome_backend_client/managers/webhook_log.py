"""Simple webhook log manager with basic CRUD"""

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.webhook_log import (
    WebhookLog as WebhookLogSchema,
)

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import WebhookLog

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.webhook_log import (
        WebhookLogFilter,
        WebhookLogSchemaCreate,
        WebhookLogSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    WebhookLogSchemaCreate = WebhookLogSchema.schemas.create
    WebhookLogSchemaUpdate = WebhookLogSchema.schemas.update
    WebhookLogFilter = WebhookLogSchema.filter


class WebhookLogManager(
    BaseCRUDManager[
        WebhookLog, WebhookLogSchemaCreate, WebhookLogSchemaUpdate, WebhookLogFilter
    ]
):
    """Simple webhook log manager with basic CRUD"""

    def __init__(self, client: "UAProjectClient"):
        super().__init__(client, "webhook-logs")
