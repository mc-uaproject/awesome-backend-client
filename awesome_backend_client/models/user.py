"""User model with methods for user operations"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Self

from uaproject_backend_schemas.models.schemas.transaction import TransactionType
from uaproject_backend_schemas.models.user import User as UserModel

from awesome_backend_client.mixins import ClientModelMixin

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.user import (
        UserSchemaCreate,
        UserSchemaResponse,
        UserSchemaUpdate,
    )

    from awesome_backend_client.models.application import Application
    from awesome_backend_client.models.application_section import ApplicationSection
    from awesome_backend_client.models.balance import Balance
    from awesome_backend_client.models.punishment import Punishment
    from awesome_backend_client.models.transaction import Transaction
else:
    UserSchemaCreate = UserModel.schemas.create
    UserSchemaUpdate = UserModel.schemas.update
    UserSchemaResponse = UserModel.schemas.response

logger = logging.getLogger(__name__)


class User(UserSchemaResponse, ClientModelMixin[UserSchemaCreate, UserSchemaUpdate]):
    """
    User model with direct inheritance from UserResponse schema.

    All schema fields are accessible directly (id, discord_id, minecraft_nickname, etc.)
    with full typing support. Provides async methods for related data and operations.
    """

    _endpoint: ClassVar[str] = "users"

    async def get_balance(self) -> Balance | None:
        """Get user's balance"""
        if self.id is None:
            return None
        return await self._client.balances.get_by_user_id(user_id=self.id, _raise=False)

    async def get_application(self) -> Application | None:
        """Get user's active application"""
        if self.id is None:
            return None
        return await self._client.applications.get_by_user_id(
            user_id=self.id, _raise=False
        )

    async def get_application_sections(
        self, application_id: int | None = None, **filters: Any
    ) -> list[ApplicationSection]:
        """Get user's application sections"""
        if application_id:
            filters["application_id"] = application_id
        else:
            application = await self.get_application()
            if not application:
                return []
            filters["application_id"] = application.id

        return await self._client.application_sections.list(**filters)

    async def get_punishments(
        self, active_only: bool = True, **filters: Any
    ) -> list[Punishment]:
        """Get user's punishments"""
        if active_only:
            filters["is_active"] = True
        filters["user_id"] = self.id
        return (
            await self._client.punishments.list(**filters)
            if hasattr(self._client, "punishments")
            else []
        )

    async def get_transactions(
        self, limit: int = 100, **filters: Any
    ) -> list[Transaction]:
        """Get user's transactions"""
        filters["user_id"] = self.id
        return await self._client.transactions.list(limit=limit, **filters)

    # Balance operations - aliases to Balance model methods
    async def add_balance(
        self, amount: float, description: str = "Manual adjustment"
    ) -> Transaction:
        """Add balance to user (alias to Balance.add)"""
        balance = await self.get_balance()
        if balance:
            return await balance.add(amount, description)

        # If no balance exists, create transaction directly
        transaction_data = {
            "recipient_id": self.id,
            "amount": amount,
            "type": TransactionType.ADJUSTMENT,
            "description": description,
        }
        return await self._client.transactions.create(transaction_data)

    async def remove_balance(
        self, amount: float, description: str = "Manual adjustment"
    ) -> Transaction:
        """Remove balance from user (alias to Balance.remove)"""
        balance = await self.get_balance()
        if balance:
            return await balance.remove(amount, description)

        # If no balance exists, create transaction directly
        return await self.add_balance(-abs(amount), description)

    async def transfer_balance(
        self, recipient_id: int, amount: float, description: str = "Transfer"
    ) -> Transaction:
        """Transfer balance to another user (alias to Balance.transfer_to_user)"""
        balance = await self.get_balance()
        if balance:
            return await balance.transfer_to_user(recipient_id, amount, description)

        # If no balance exists, create transaction directly
        transaction_data = {
            "user_id": self.id,
            "recipient_id": recipient_id,
            "amount": amount,
            "type": TransactionType.TRANSFER,
            "description": description,
        }
        return await self._client.transactions.create(transaction_data)

    # Custom endpoints for User
    async def set_minecraft_nickname(self, nickname: str) -> Self:
        """Set minecraft nickname for user"""
        data = await self._client.http.post(
            f"/users/{self.id}/set-minecraft-nickname", json={"nickname": nickname}
        )

        if isinstance(data, list | str):
            msg = f"Expected a single user, got {type(data)}"
            raise TypeError(msg)

        self._update_from_dict(data)
        return self
