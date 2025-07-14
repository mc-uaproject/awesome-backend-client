"""Punishment model with methods for punishment operations"""

import logging
from typing import TYPE_CHECKING, Optional

from uaproject_backend_schemas.models import (
    Punishment as PunishmentSchema,
)
from uaproject_backend_schemas.models import (
    User as UserSchema,
)

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.punishment import PunishmentSchemaResponse

    from awesome_backend_client.client import UAProjectClient
    from awesome_backend_client.models.user import User
else:
    PunishmentSchemaResponse = PunishmentSchema.schemas.response

logger = logging.getLogger(__name__)


class Punishment(BaseBackendModel, PunishmentSchemaResponse):
    """
    Punishment model with methods for punishment operations
    """

    def __init__(
        self, punishment_schema: PunishmentSchemaResponse, *, client: "UAProjectClient"
    ):
        super().__init__(punishment_schema, client=client)

    async def refresh(self):
        """Refresh punishment data from API"""
        try:
            fresh_data = await self._client.punishments.get(self.id)
            self._schema = PunishmentSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh punishment {self.id}: {e}")

    async def edit(self, **fields) -> "Punishment":
        """Edit punishment fields"""
        updated_data = await self._client.punishments.update(self.id, fields)
        self._schema = PunishmentSchema.model_validate(updated_data)
        return self

    async def revoke(self, reason: str = "Manually revoked") -> "Punishment":
        """Revoke this punishment"""
        updated_data = await self._client.punishments.update(
            self.id, {"is_active": False, "revoke_reason": reason}
        )
        self._schema = PunishmentSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional["User"]:
        """Get the user who received this punishment"""
        user_data = await self._client.users.get(self.user_id)
        from awesome_backend_client.models.user import User

        return User(UserSchema.model_validate(user_data), client=self._client)

    def __str__(self) -> str:
        return f"Punishment(id={self.id}, type='{self.type}', active={self.is_active})"

    def __repr__(self) -> str:
        return f"<Punishment id={self.id} type='{self.type}' active={self.is_active}>"
