"""ApplicationSection model with methods for application section operations"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, Self

from uaproject_backend_schemas.models.application_section import (
    ApplicationSection as ApplicationSectionModel,
)

from awesome_backend_client.mixins import ClientModelMixin

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application_section import (
        ApplicationSectionSchemaCreate,
        ApplicationSectionSchemaResponse,
        ApplicationSectionSchemaUpdate,
    )

    from awesome_backend_client.models.application import Application
    from awesome_backend_client.models.user import User
else:
    ApplicationSectionSchemaCreate = ApplicationSectionModel.schemas.create
    ApplicationSectionSchemaUpdate = ApplicationSectionModel.schemas.update
    ApplicationSectionSchemaResponse = ApplicationSectionModel.schemas.response

logger = logging.getLogger(__name__)


class ApplicationSection(
    ApplicationSectionSchemaResponse,
    ClientModelMixin[ApplicationSectionSchemaCreate, ApplicationSectionSchemaUpdate],
):
    """
    ApplicationSection model with direct inheritance from ApplicationSectionResponse schema.

    All schema fields are accessible directly (id, application_id, server_type, status, etc.)
    with full typing support. Provides async methods for application section operations.
    """

    _endpoint: ClassVar[str] = "application-sections"

    async def get_application(self) -> Application | None:
        """Get the application this section belongs to"""
        if self.application_id is None:
            return None
        return await self._client.applications.get(self.application_id, _raise=False)

    async def get_reviewer(self) -> User | None:
        """Get the user who reviewed this section"""
        if self.reviewed_by is None:
            return None
        return await self._client.users.get(self.reviewed_by, _raise=False)

    async def approve(self, reviewer_id: int | None = None) -> Self:
        """Approve this application section"""
        if reviewer_id is None:
            if not hasattr(self._client, "impersonate_user_id"):
                msg = "reviewer_id is required when not impersonating"
                raise ValueError(msg)
            reviewer_id = self._client.impersonate_user_id

        data = await self._client.http.post(
            f"/application-sections/{self.id}/approve",
            json={"reviewer_id": reviewer_id},
        )

        if isinstance(data, list | str):
            msg = f"Expected a single application section, got {type(data)}"
            raise TypeError(msg)

        self._update_from_dict(data)
        return self

    async def reject(self, reason: str, reviewer_id: int | None = None) -> Self:
        """Reject this application section"""
        if reviewer_id is None:
            if not hasattr(self._client, "impersonate_user_id"):
                msg = "reviewer_id is required when not impersonating"
                raise ValueError(msg)
            reviewer_id = self._client.impersonate_user_id

        data = await self._client.http.post(
            f"/application-sections/{self.id}/reject",
            json={"reason": reason, "reviewer_id": reviewer_id},
        )

        if isinstance(data, list | str):
            msg = f"Expected a single application section, got {type(data)}"
            raise TypeError(msg)

        self._update_from_dict(data)
        return self
