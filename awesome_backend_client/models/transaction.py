"""Transaction model wrapper for UAProject backend"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from awesome_backend_client.models.user import User

from uaproject_backend_schemas.models.transaction import Transaction as TransactionSchema

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.transaction import (
        TransactionFilter,
        TransactionSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    TransactionFilter = TransactionSchema.filter
    TransactionSchemaUpdate = TransactionSchema.schemas.update


class Transaction(BaseBackendModel[TransactionSchema, TransactionFilter, TransactionSchemaUpdate]):
    """Transaction model with convenient methods"""

    _endpoint = "transactions"

    def __init__(self, schema_obj: TransactionSchema, *, client: UAProjectClient):
        super().__init__(schema_obj, client=client)

    async def get_user(self) -> User:
        """Get the user who created this transaction"""
        result = await self._client.users.get(self.user_id)
        if isinstance(result, User):
            return result
        raise TypeError(f"Expected User, got {type(result)}")

    async def get_recipient(self) -> User:
        """Get the transaction recipient"""
        result = await self._client.users.get(self.recipient_id)
        if isinstance(result, User):
            return result
        raise TypeError(f"Expected User, got {type(result)}")

    def __str__(self) -> str:
        return f"Transaction(id={self.id}, type={self.type}, amount={self.amount})"

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} user_id={self.user_id} recipient_id={self.recipient_id} amount={self.amount} type='{self.type}'>"