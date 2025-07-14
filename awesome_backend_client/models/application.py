"""Application model with methods for application operations"""

import logging
from typing import TYPE_CHECKING, Optional

from uaproject_backend_schemas.models import (
    Application as ApplicationSchema,
)
from uaproject_backend_schemas.models import (
    Service as ServiceSchema,
)
from uaproject_backend_schemas.models import (
    User as UserSchema,
)

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application import ApplicationSchemaResponse

    from awesome_backend_client.client import UAProjectClient
    from awesome_backend_client.models import (
        Application,
        Service,
        User,
    )
else:
    ApplicationSchemaResponse = ApplicationSchema.schemas.response

logger = logging.getLogger(__name__)


class Application(BaseBackendModel, ApplicationSchemaResponse):
    """
    Application model with methods for application operations

    Wraps ApplicationSchema from uaproject-backend-schemas and adds convenience methods.
    """

    def __init__(
        self, app_schema: ApplicationSchemaResponse, *, client: "UAProjectClient"
    ):
        super().__init__(app_schema, client=client)

    async def refresh(self):
        """Refresh application data from API"""
        try:
            fresh_data = await self._client.applications.get(self.id)
            self._schema = ApplicationSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh application {self.id}: {e}")

    async def approve(self, reason: str = "") -> "Application":
        """Approve this application"""
        updated_data = await self._client.applications.update(
            self.id, {"status": "approved", "admin_notes": reason}
        )
        self._schema = ApplicationSchema.model_validate(updated_data)
        return self

    async def reject(self, reason: str = "") -> "Application":
        """Reject this application"""
        updated_data = await self._client.applications.update(
            self.id, {"status": "rejected", "admin_notes": reason}
        )
        self._schema = ApplicationSchema.model_validate(updated_data)
        return self

    async def edit(self, **fields) -> "Application":
        """Edit application fields"""
        updated_data = await self._client.applications.update(self.id, fields)
        self._schema = ApplicationSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional["User"]:
        """Get the user who submitted this application"""
        try:
            user_data = await self._client.users.get(self.user_id)
            from .user import User

            return User(UserSchema.model_validate(user_data), client=self._client)
        except Exception:
            return None

    async def get_service(self) -> Optional["Service"]:
        """Get the service this application is for"""
        try:
            service_data = await self._client.services.get(self.service_id)
            from .service import Service

            return Service(
                ServiceSchema.model_validate(service_data), client=self._client
            )
        except Exception:
            return None

    def __str__(self) -> str:
        return (
            f"Application(id={self.id}, status='{self.status}', user_id={self.user_id})"
        )

    def __repr__(self) -> str:
        return (
            f"<Application id={self.id} status='{self.status}' user_id={self.user_id}>"
        )
