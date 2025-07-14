"""Application resource manager with custom methods"""

from typing import TYPE_CHECKING, Any

from uaproject_backend_schemas.models.application import Application as ApplicationModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Application

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application import (
        ApplicationFilter,
        ApplicationSchemaCreate,
        ApplicationSchemaUpdate,
    )
else:
    ApplicationSchemaCreate = ApplicationModel.schemas.create
    ApplicationSchemaUpdate = ApplicationModel.schemas.update
    ApplicationFilter = ApplicationModel.filter


class ApplicationManager(
    BaseCRUDManager[
        Application,
        ApplicationSchemaCreate,
        ApplicationSchemaUpdate,
        ApplicationFilter,
    ]
):
    """Application resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "applications", Application)

    async def get_base(self) -> dict[str, Any]:
        """Get base application template"""
        return await self.client.http.get("/applications/base")

    async def get_evervault(self) -> dict[str, Any]:
        """Get evervault application"""
        return await self.client.http.get("/applications/evervault")

    async def get_v2(self) -> list[Application]:
        """Get v2 applications"""
        data = await self.client.http.get("/applications/v2")
        return self._convert_to_models(data)

    async def get_count(self, **filters) -> dict[str, Any]:
        """Get application count with filters"""
        return await self.client.http.get("/applications/list/count", params=filters)

    async def search(self, **params) -> list[Application]:
        """Search applications"""
        data = await self.client.http.get("/applications/list/search", params=params)
        return self._convert_to_models(data)

    async def submit_section(
        self, application_id: int, section_name: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Submit application section"""
        return await self.client.http.post(
            f"/applications/{application_id}/section/{section_name}/submit",
            data=data,
        )
