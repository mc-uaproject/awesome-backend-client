"""Transaction model with methods for transaction operations"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from uaproject_backend_schemas.models.transaction import Transaction as TransactionModel

from awesome_backend_client.mixins import ClientModelMixin

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.transaction import (
        TransactionSchemaCreate,
        TransactionSchemaResponse,
        TransactionSchemaUpdate,
    )

    from awesome_backend_client.models.service import Service
    from awesome_backend_client.models.user import User
else:
    TransactionSchemaCreate = TransactionModel.schemas.create
    TransactionSchemaUpdate = TransactionModel.schemas.update
    TransactionSchemaResponse = TransactionModel.schemas.response

logger = logging.getLogger(__name__)


class Transaction(
    TransactionSchemaResponse,
    ClientModelMixin[TransactionSchemaCreate, TransactionSchemaUpdate],
):
    """
    Transaction model with direct inheritance from TransactionResponse schema.

    All schema fields are accessible directly (id, user_id, recipient_id, amount, type, etc.)
    with full typing support. Provides async methods for transaction operations.
    """

    _endpoint: ClassVar[str] = "transactions"

    async def get_user(self) -> User | None:
        """Get the user who created this transaction"""
        if self.user_id is None:
            return None
        return await self._client.users.get(self.user_id, _raise=False)

    async def get_recipient(self) -> User | None:
        """Get the transaction recipient"""
        if self.recipient_id is None:
            return None
        return await self._client.users.get(self.recipient_id, _raise=False)

    async def get_service(self) -> Service | None:
        """Get the service if this is a purchase transaction"""
        if self.service_id is None:
            return None
        return await self._client.services.get(self.service_id, _raise=False)

    async def get_related_transactions(self, limit: int = 10) -> list[Transaction]:
        """Get related transactions (same user or recipient)"""
        filters = {}
        if self.user_id:
            filters["user_id"] = self.user_id
        if self.recipient_id and self.recipient_id != self.user_id:
            filters["recipient_id"] = self.recipient_id

        return await self._client.transactions.list(limit=limit, **filters)
