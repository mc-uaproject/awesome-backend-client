"""Balance model with methods for balance operations"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from uaproject_backend_schemas.models.balance import Balance as BalanceModel
from uaproject_backend_schemas.models.schemas.transaction import TransactionType

from awesome_backend_client.mixins import ClientModelMixin

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.balance import (
        BalanceSchemaCreate,
        BalanceSchemaResponse,
        BalanceSchemaUpdate,
    )

    from awesome_backend_client.models.transaction import Transaction
    from awesome_backend_client.models.user import User
else:
    BalanceSchemaCreate = BalanceModel.schemas.create
    BalanceSchemaUpdate = BalanceModel.schemas.update
    BalanceSchemaResponse = BalanceModel.schemas.response

logger = logging.getLogger(__name__)


class Balance(
    BalanceSchemaResponse, ClientModelMixin[BalanceSchemaCreate, BalanceSchemaUpdate]
):
    """
    Balance model with direct inheritance from BalanceResponse schema.

    All schema fields are accessible directly (id, user_id, amount, etc.)
    with full typing support. Provides async methods for balance operations.
    """

    _endpoint: ClassVar[str] = "balances"

    async def get_user(self) -> User | None:
        """Get user associated with this balance"""
        if self.user_id is None:
            return None
        return await self._client.users.get(self.user_id, _raise=False)

    async def get_transactions(
        self, limit: int = 100, **filters: Any
    ) -> list[Transaction]:
        """Get transactions for this balance"""
        if self.user_id is None:
            return []
        filters["user_id"] = self.user_id
        return await self._client.transactions.list(limit=limit, **filters)

    async def add(
        self, amount: float, description: str = "Manual adjustment"
    ) -> Transaction:
        """Add amount to balance"""
        if self.user_id is None:
            msg = "Cannot add amount to balance without user_id"
            raise ValueError(msg)

        transaction_data = {
            "recipient_id": self.user_id,
            "amount": amount,
            "type": TransactionType.ADJUSTMENT,
            "description": description,
        }
        return await self._client.transactions.create(transaction_data)

    async def remove(
        self, amount: float, description: str = "Manual adjustment"
    ) -> Transaction:
        """Remove amount from balance"""
        return await self.add(-abs(amount), description)

    async def transfer_to_user(
        self, recipient_id: int, amount: float, description: str = "Transfer"
    ) -> Transaction:
        """Transfer amount to another user"""
        if self.user_id is None:
            msg = "Cannot transfer from balance without user_id"
            raise ValueError(msg)

        transaction_data = {
            "user_id": self.user_id,
            "recipient_id": recipient_id,
            "amount": amount,
            "type": TransactionType.TRANSFER,
            "description": description,
        }
        return await self._client.transactions.create(transaction_data)
