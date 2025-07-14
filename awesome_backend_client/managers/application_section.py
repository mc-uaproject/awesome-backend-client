"""Application section resource manager with custom methods"""

from typing import TYPE_CHECKING, Any

from uaproject_backend_schemas.models.application_section import ApplicationSection

from awesome_backend_client.base import BaseCRUDManager

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application_section import (
        ApplicationSectionFilter,
        ApplicationSectionSchemaCreate,
        ApplicationSectionSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    ApplicationSectionSchemaCreate = ApplicationSection.schemas.create
    ApplicationSectionSchemaUpdate = ApplicationSection.schemas.update
    ApplicationSectionFilter = ApplicationSection.filter


class ApplicationSectionManager(
    BaseCRUDManager[
        ApplicationSection,
        ApplicationSectionSchemaCreate,
        ApplicationSectionSchemaUpdate,
        ApplicationSectionFilter,
    ]
):
    """Application section resource manager with custom methods"""

    def __init__(self, client: "UAProjectClient"):
        super().__init__(client, "application-sections")

    async def create(
        self,
        data: dict[str, Any] | ApplicationSectionSchemaCreate,
    ) -> dict[str, Any]:
        """Create new application section"""
        return await super().create(data)

    async def update(
        self,
        item_id: int | str,
        data: dict[str, Any] | ApplicationSectionSchemaUpdate,
    ) -> dict[str, Any]:
        """Update application section"""
        return await super().update(item_id, data)

    async def get_by_application(self, application_id: int) -> list[dict[str, Any]]:
        """Get sections for application"""
        return await self.client.http.get(
            f"/application-sections/application/{application_id}"
        )

    async def get_by_application_and_server(
        self, application_id: int, server_type: str
    ) -> list[dict[str, Any]]:
        """Get sections for application and server type"""
        return await self.client.http.get(
            f"/application-sections/application/{application_id}/server/{server_type}"
        )
