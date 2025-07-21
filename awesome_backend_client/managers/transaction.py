"""Transaction resource manager with custom methods"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.transaction import Transaction as TransactionModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Transaction

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.transaction import (
        TransactionFilter,
        TransactionSchemaCreate,
        TransactionSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    TransactionSchemaCreate = TransactionModel.schemas.create
    TransactionSchemaUpdate = TransactionModel.schemas.update
    TransactionFilter = TransactionModel.filter


class TransactionManager(
    BaseCRUDManager[
        Transaction, TransactionSchemaCreate, TransactionSchemaUpdate, TransactionFilter
    ]
):
    """Transaction resource manager with custom methods"""

    def __init__(self, client: UAProjectClient) -> None:
        super().__init__(client, "transactions", Transaction)

    async def get_user_summary(self, user_id: int) -> dict:
        """Get transaction summary for a user"""
        data = await self.client.http.get(f"/transactions/user/{user_id}/summary")
        if isinstance(data, dict):
            return data
        msg = f"Expected dict response, got {type(data)}"
        raise TypeError(msg)
