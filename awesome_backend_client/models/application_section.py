"""ApplicationSection model wrapper for UAProject backend"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from awesome_backend_client.models.application import Application
    from awesome_backend_client.models.user import User

from uaproject_backend_schemas.models.application_section import ApplicationSection as ApplicationSectionSchema

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application_section import (
        ApplicationSectionFilter,
        ApplicationSectionSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    ApplicationSectionFilter = ApplicationSectionSchema.filter
    ApplicationSectionSchemaUpdate = ApplicationSectionSchema.schemas.update


class ApplicationSection(BaseBackendModel[ApplicationSectionSchema, ApplicationSectionFilter, ApplicationSectionSchemaUpdate]):
    """ApplicationSection model with convenient methods"""

    _endpoint = "application-sections"

    def __init__(self, schema_obj: ApplicationSectionSchema, *, client: UAProjectClient):
        super().__init__(schema_obj, client=client)

    async def get_application(self) -> Application:
        """Get the application this section belongs to"""
        result = await self._client.applications.get(self.application_id)
        if isinstance(result, Application):
            return result
        raise TypeError(f"Expected Application, got {type(result)}")

    async def get_reviewer(self) -> User | None:
        """Get the user who reviewed this section"""
        if self.reviewed_by:
            result = await self._client.users.get(self.reviewed_by)
            if isinstance(result, User):
                return result
            raise TypeError(f"Expected User, got {type(result)}")
        return None

    def __str__(self) -> str:
        return f"ApplicationSection(id={self.id}, application_id={self.application_id}, server_type={self.server_type}, status={self.status})"

    def __repr__(self) -> str:
        return f"<ApplicationSection id={self.id} application_id={self.application_id} server_type='{self.server_type}' status='{self.status}'>"