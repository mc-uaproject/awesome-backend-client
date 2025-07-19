"""User model with methods for user operations"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from uaproject_backend_schemas.models.user import User as UserModel

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.application import (
        Application as ApplicationSchema,
    )
    from uaproject_backend_schemas.models.balance import Balance as BalanceSchema
    from uaproject_backend_schemas.models.punishment import (
        Punishment as PunishmentSchema,
    )
    from uaproject_backend_schemas.models.transaction import (
        Transaction as TransactionSchema,
    )
    from uaproject_backend_schemas.models.user import (
        UserFilter,
        UserSchemaResponse,
        UserSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    UserSchemaResponse = UserModel.schemas.response
    UserFilter = UserModel.filter
    UserSchemaUpdate = UserModel.schemas.update
    BalanceSchema = None
    PunishmentSchema = None
    TransactionSchema = None
    ApplicationSchema = None

logger = logging.getLogger(__name__)


class User(BaseBackendModel):
    """
    User model with methods for user operations

    Wraps UserSchema from uaproject-backend-schemas and adds convenience methods.
    All UserSchema properties are accessible directly
    (id, discord_id, minecraft_nickname, etc.)
    """

    _endpoint = "users"

    def __init__(self, user_schema: UserSchemaResponse, *, client: UAProjectClient):
        BaseBackendModel.__init__(self, user_schema, client=client)

    @property
    async def balance(self) -> Any | None:
        """Get user's balance"""
        return await self.get("balance")

    async def applications(self, status: str | None = None, **filters) -> list[Any]:
        """Get user's applications"""
        if status:
            filters["status"] = status
        return await self.get("applications", filters=filters)

    async def punishments(self, active_only: bool = True, **filters) -> list[Any]:
        """Get user's punishments"""
        if active_only:
            filters["is_active"] = True
        return await self.get("punishments", filters=filters)

    async def transactions(self, limit: int = 100, **filters) -> list[Any]:
        """Get user's transactions"""
        return await self.get("transactions", filters=filters, limit=limit)

    async def add_balance(
        self, amount: float, reason: str = "Manual adjustment"
    ) -> Any:
        """Add balance to user"""
        return await self._client.http.post(
            "/transactions",
            json={
                "user_id": self.id,
                "amount": amount,
                "type": "adjustment",
                "reason": reason,
            },
        )

    async def remove_balance(
        self, amount: float, reason: str = "Manual adjustment"
    ) -> Any:
        """Remove balance from user"""
        return await self._client.http.post(
            "/transactions",
            json={
                "user_id": self.id,
                "amount": -abs(amount),
                "type": "adjustment",
                "reason": reason,
            },
        )

    # Custom endpoints for User
    async def set_minecraft_nickname(self, nickname: str) -> User:
        """Set minecraft nickname for user"""
        data = await self._client.http.post(
            f"/users/{self.id}/set-minecraft-nickname", json={"nickname": nickname}
        )

        if isinstance(data, list | str):
            msg = f"Expected a single user, got {type(data)}"
            raise TypeError(msg)

        self._update_from_dict(data)
        return self

    def __str__(self) -> str:
        nickname = self.get_attr("minecraft_nickname")
        return f"User(id={self.id}, nickname='{nickname or 'Unknown'}')"

    def __repr__(self) -> str:
        nickname = self.get_attr("minecraft_nickname")
        return f"<User id={self.id} nickname='{nickname or 'Unknown'}'>"
