"""Service model with methods for service operations"""

import logging
from typing import TYPE_CHECKING, Optional

from uaproject_backend_schemas.models import (
    Application as ApplicationSchema,
)
from uaproject_backend_schemas.models import (
    Service as ServiceSchema,
)

from awesome_backend_client.base import BaseBackendModel
from awesome_backend_client.models import Application

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.service import ServiceSchemaResponse

    from awesome_backend_client.client import UAProjectClient
else:
    ServiceSchemaResponse = ServiceSchema.schemas.response

logger = logging.getLogger(__name__)


class Service(BaseBackendModel, ServiceSchemaResponse):
    """
    Service model with methods for service operations
    """

    def __init__(
        self, service_schema: ServiceSchemaResponse, *, client: "UAProjectClient"
    ):
        super().__init__(service_schema, client=client)

    async def refresh(self):
        """Refresh service data from API"""
        try:
            fresh_data = await self._client.services.get(self.id)
            self._schema = ServiceSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh service {self.id}: {e}")

    async def edit(self, **fields) -> "Service":
        """Edit service fields"""
        updated_data = await self._client.services.update(self.id, fields)
        self._schema = ServiceSchema.model_validate(updated_data)
        return self

    async def get_applications(
        self, *, status: Optional[str] = None, limit: int = 50
    ) -> list[Application]:
        """Get applications for this service"""
        try:
            filters = {"service_id": self.id}
            if status:
                filters["status"] = status

            apps_data = await self._client.applications.get_many(
                filters=filters, limit=limit
            )

            return [
                Application(ApplicationSchema.model_validate(app), client=self._client)
                for app in apps_data
            ]
        except Exception:
            return []

    def __str__(self) -> str:
        return f"Service(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        return f"<Service id={self.id} name='{self.name}'>"
