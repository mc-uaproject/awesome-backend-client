"""Application model wrapper for UAProject backend"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from awesome_backend_client.models.application_section import ApplicationSection
    from awesome_backend_client.models.user import User

from uaproject_backend_schemas.models.application import Application as ApplicationSchema

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application import (
        ApplicationFilter,
        ApplicationSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    ApplicationFilter = ApplicationSchema.filter
    ApplicationSchemaUpdate = ApplicationSchema.schemas.update


class Application(BaseBackendModel[ApplicationSchema, ApplicationFilter, ApplicationSchemaUpdate]):
    """Application model with convenient methods"""

    _endpoint = "applications"

    def __init__(self, schema_obj: ApplicationSchema, *, client: UAProjectClient):
        super().__init__(schema_obj, client=client)

    async def get_user(self) -> User:
        """Get the user who submitted this application"""
        result = await self._client.users.get(self.user_id)
        if isinstance(result, User):
            return result
        raise TypeError(f"Expected User, got {type(result)}")

    async def get_sections(self) -> list[ApplicationSection]:
        """Get application sections"""
        return await self._client.application_sections.get_by_application_id(self.id)

    def __str__(self) -> str:
        return f"Application(id={self.id}, user_id={self.user_id}, status={self.status})"

    def __repr__(self) -> str:
        return f"<Application id={self.id} user_id={self.user_id} status='{self.status}'>"