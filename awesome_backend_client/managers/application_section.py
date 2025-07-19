"""ApplicationSection resource manager with custom methods"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.application_section import ApplicationSection as ApplicationSectionModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import ApplicationSection

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application_section import (
        ApplicationSectionFilter,
        ApplicationSectionSchemaCreate,
        ApplicationSectionSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    ApplicationSectionSchemaCreate = ApplicationSectionModel.schemas.create
    ApplicationSectionSchemaUpdate = ApplicationSectionModel.schemas.update
    ApplicationSectionFilter = ApplicationSectionModel.filter


class ApplicationSectionManager(
    BaseCRUDManager[ApplicationSection, ApplicationSectionSchemaCreate, ApplicationSectionSchemaUpdate, ApplicationSectionFilter]
):
    """ApplicationSection resource manager with custom methods"""

    def __init__(self, client: UAProjectClient) -> None:
        super().__init__(client, "application-sections", ApplicationSection)

    async def get_by_application_id(self, application_id: int, *, server_type: str | None = None) -> list[ApplicationSection]:
        """Get sections by application ID, optionally filtered by server type"""
        filters = {"application_id": application_id}
        if server_type:
            filters["server_type"] = server_type
        return await self.list(**filters)

    async def get_by_application_and_server(self, application_id: int, server_type: str) -> ApplicationSection | None:
        """Get specific section by application ID and server type"""
        data = await self.client.http.get(f"/application-sections/application/{application_id}/server/{server_type}")
        if isinstance(data, dict):
            return self._convert_to_model(data)
        return None