"""Application resource manager with custom methods"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.application import Application as ApplicationModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Application

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application import (
        ApplicationFilter,
        ApplicationSchemaCreate,
        ApplicationSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    ApplicationSchemaCreate = ApplicationModel.schemas.create
    ApplicationSchemaUpdate = ApplicationModel.schemas.update
    ApplicationFilter = ApplicationModel.filter


class ApplicationManager(
    BaseCRUDManager[Application, ApplicationSchemaCreate, ApplicationSchemaUpdate, ApplicationFilter]
):
    """Application resource manager with custom methods"""

    def __init__(self, client: UAProjectClient) -> None:
        super().__init__(client, "applications", Application)

    async def get_by_user_id(self, user_id: int) -> Application:
        """Get application by user ID (assumes user_id is unique for applications)"""
        result = await self.get_by(user_id=user_id)
        if isinstance(result, Application):
            return result
        raise TypeError(f"Expected Application, got {type(result)}")

    async def get_many(
        self,
        *,
        filters: dict[str, str | int | bool] | None = None,
        skip: int = 0,
        limit: int = 100,
        **extra_filters: str | int | bool,
    ) -> list[Application]:
        """Get multiple applications with filters"""
        all_filters = {**(filters or {}), **extra_filters}
        return await self.list(skip=skip, limit=limit, **all_filters)

    async def search(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        **search_params: str | int | bool,
    ) -> list[Application]:
        """Search applications using /applications/list/search endpoint"""
        params = {"skip": skip, "limit": limit, **search_params}
        data = await self.client.http.get("/applications/list/search", params=params)
        if isinstance(data, list):
            return self._convert_to_models(data)
        msg = f"Expected list response, got {type(data)}"
        raise TypeError(msg)

    async def count(self, **filters: str | int | bool) -> dict:
        """Get application count using /applications/list/count endpoint"""
        data = await self.client.http.get("/applications/list/count", params=filters)
        if isinstance(data, dict):
            return data
        msg = f"Expected dict response, got {type(data)}"
        raise TypeError(msg)