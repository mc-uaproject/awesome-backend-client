"""Balance model with methods for balance operations"""

import logging
from typing import TYPE_CHECKING, Optional

from uaproject_backend_schemas.models import (
    Balance as BalanceSchema,
)
from uaproject_backend_schemas.models import (
    User as UserSchema,
)

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.balance import BalanceSchemaResponse

    from awesome_backend_client.client import UAProjectClient
    from awesome_backend_client.models.user import User
else:
    BalanceSchemaResponse = BalanceSchema.schemas.response

logger = logging.getLogger(__name__)


class Balance(BaseBackendModel, BalanceSchemaResponse):
    """
    Balance model with methods for balance operations
    """

    def __init__(
        self, balance_schema: BalanceSchemaResponse, *, client: "UAProjectClient"
    ):
        super().__init__(balance_schema, client=client)

    async def refresh(self):
        """Refresh balance data from API"""
        try:
            fresh_data = await self._client.balances.get(self.id)
            self._schema = BalanceSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh balance {self.id}: {e}")

    async def edit(self, **fields) -> "Balance":
        """Edit balance fields"""
        updated_data = await self._client.balances.update(self.id, fields)
        self._schema = BalanceSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional["User"]:
        """Get the user who owns this balance"""
        user_data = await self._client.users.get(self.user_id)
        from awesome_backend_client.models.user import User

        return User(UserSchema.model_validate(user_data), client=self._client)

    def __str__(self) -> str:
        return f"Balance(id={self.id}, amount={self.amount}, user_id={self.user_id})"

    def __repr__(self) -> str:
        return f"<Balance id={self.id} amount={self.amount} user_id={self.user_id}>"
