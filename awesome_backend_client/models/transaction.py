"""Transaction model with methods for transaction operations"""

import logging
from typing import TYPE_CHECKING, Optional

from uaproject_backend_schemas.models import (
    Transaction as TransactionSchema,
)
from uaproject_backend_schemas.models import (
    User as UserSchema,
)

from awesome_backend_client.base import BaseBackendModel
from awesome_backend_client.models.user import User

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.transaction import TransactionSchemaResponse

    from awesome_backend_client.client import UAProjectClient
else:
    TransactionSchemaResponse = TransactionSchema.schemas.response

logger = logging.getLogger(__name__)


class Transaction(BaseBackendModel, TransactionSchemaResponse):
    """
    Transaction model with methods for transaction operations
    """

    def __init__(
        self,
        transaction_schema: TransactionSchemaResponse,
        *,
        client: "UAProjectClient",
    ):
        super().__init__(transaction_schema, client=client)

    async def refresh(self):
        """Refresh transaction data from API"""
        try:
            fresh_data = await self._client.transactions.get(self.id)
            self._schema = TransactionSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh transaction {self.id}: {e}")

    async def edit(self, **fields) -> "Transaction":
        """Edit transaction fields"""
        updated_data = await self._client.transactions.update(self.id, fields)
        self._schema = TransactionSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional[User]:
        """Get the user who made this transaction"""
        try:
            user_data = await self._client.users.get(self.user_id)

            return User(UserSchema.model_validate(user_data), client=self._client)
        except Exception:
            return None

    def __str__(self) -> str:
        return f"Transaction(id={self.id}, amount={self.amount}, type='{self.type}')"

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} amount={self.amount} type='{self.type}'>"
