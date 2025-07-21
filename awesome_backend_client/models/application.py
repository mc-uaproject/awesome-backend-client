"""Application model with methods for application operations"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from uaproject_backend_schemas.models.application import Application as ApplicationModel

from awesome_backend_client.mixins import ClientModelMixin

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application import (
        ApplicationSchemaCreate,
        ApplicationSchemaResponse,
        ApplicationSchemaUpdate,
    )

    from awesome_backend_client.models.application_section import ApplicationSection
    from awesome_backend_client.models.user import User
else:
    ApplicationSchemaCreate = ApplicationModel.schemas.create
    ApplicationSchemaUpdate = ApplicationModel.schemas.update
    ApplicationSchemaResponse = ApplicationModel.schemas.response

logger = logging.getLogger(__name__)


class Application(
    ApplicationSchemaResponse,
    ClientModelMixin[ApplicationSchemaCreate, ApplicationSchemaUpdate],
):
    """
    Application model with direct inheritance from ApplicationResponse schema.

    All schema fields are accessible directly (id, user_id, status, etc.)
    with full typing support. Provides async methods for application operations.
    """

    _endpoint: ClassVar[str] = "applications"

    async def get_user(self) -> User | None:
        """Get the user who submitted this application"""
        if self.user_id is None:
            return None
        return await self._client.users.get(self.user_id, _raise=False)

    async def get_sections(self, **filters: Any) -> list[ApplicationSection]:
        """Get application sections"""
        if self.id is None:
            return []
        filters["application_id"] = self.id
        return await self._client.application_sections.list(**filters)