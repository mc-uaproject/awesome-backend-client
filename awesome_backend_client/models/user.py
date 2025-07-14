"""User model with methods for user operations"""

import logging
from typing import TYPE_CHECKING, Optional

from uaproject_backend_schemas.models import (
    Application as ApplicationSchema,
)
from uaproject_backend_schemas.models import (
    Balance as BalanceSchema,
)
from uaproject_backend_schemas.models import (
    Punishment as PunishmentSchema,
)
from uaproject_backend_schemas.models import (
    Transaction as TransactionSchema,
)
from uaproject_backend_schemas.models import (
    User as UserSchema,
)

from awesome_backend_client.base import BaseBackendModel
from awesome_backend_client.models.application import Application
from awesome_backend_client.models.balance import Balance
from awesome_backend_client.models.punishment import Punishment
from awesome_backend_client.models.transaction import Transaction

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.user import UserSchemaResponse

    from awesome_backend_client.client import UAProjectClient

else:
    UserSchemaResponse = UserSchema.schemas.response

logger = logging.getLogger(__name__)


class User(BaseBackendModel, UserSchemaResponse):
    """
    User model with methods for user operations

    Wraps UserSchema from uaproject-backend-schemas and adds convenience methods.
    All UserSchema properties are accessible directly
    (id, discord_id, minecraft_nickname, etc.)
    """

    def __init__(self, user_schema: UserSchemaResponse, *, client: "UAProjectClient"):
        super().__init__(user_schema, client=client)

    async def refresh(self):
        """Refresh user data from API"""
        try:
            fresh_data = await self._client.users.get(self.id)
            # Convert dict response to UserSchema
            self._schema = UserSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh user {self.id}: {e}")

    async def edit(self, **fields) -> "User":
        """Edit user fields (discord.py style)"""
        updated_data = await self._client.users.update(self.id, fields)
        self._schema = UserSchema.model_validate(updated_data)
        return self

    async def delete(self) -> bool:
        """Delete user"""
        return await self._client.users.delete(self.id)

    async def get_balance(self) -> Optional[Balance]:
        """Get user's balance"""
        balance_data = await self._client.balances.list(filters={"user_id": self.id})
        if balance_data:
            balance_schema = BalanceSchema.model_validate(balance_data[0])
            return Balance(balance_schema, client=self._client)

    async def get_application(self) -> list[Application]:
        """Get user's applications"""
        apps_data = await self._client.applications.list(filters={"user_id": self.id})

        return Application(
            ApplicationSchema.model_validate(apps_data[0]), client=self._client
        )

    async def get_punishments(self, active_only: bool = True) -> list[Punishment]:
        """Get user's punishments"""
        filters = {"user_id": self.id}
        if active_only:
            filters["is_active"] = True

        punishments_data = await self._client.punishments.list(filters=filters)

        return [
            Punishment(PunishmentSchema.model_validate(p), client=self._client)
            for p in punishments_data
        ]

    async def add_balance(
        self, amount: float, reason: str = "Manual adjustment"
    ) -> Transaction:
        """Add balance to user"""
        transaction_data = await self._client.transactions.create(
            {
                "user_id": self.id,
                "amount": amount,
                "type": "adjustment",
                "reason": reason,
            }
        )

        transaction_schema = TransactionSchema.model_validate(transaction_data)
        return Transaction(transaction_schema, client=self._client)

    async def remove_balance(
        self, amount: float, reason: str = "Manual adjustment"
    ) -> Transaction:
        """Remove balance from user"""
        transaction_data = await self._client.transactions.create(
            {
                "user_id": self.id,
                "amount": -abs(amount),
                "type": "adjustment",
                "reason": reason,
            }
        )

        transaction_schema = TransactionSchema.model_validate(transaction_data)
        return Transaction(transaction_schema, client=self._client)

    def __str__(self) -> str:
        # Use minecraft_nickname if available, fallback to id
        nickname = getattr(self._schema, "minecraft_nickname", None)
        return f"User(id={self.id}, nickname='{nickname or 'Unknown'}')"

    def __repr__(self) -> str:
        nickname = getattr(self._schema, "minecraft_nickname", None)
        return f"<User id={self.id} nickname='{nickname or 'Unknown'}'>"
