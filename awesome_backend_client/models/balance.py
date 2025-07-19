"""Balance model wrapper for UAProject backend"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.balance import Balance as BalanceSchema

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.balance import (
        BalanceFilter,
        BalanceSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    BalanceFilter = BalanceSchema.filter
    BalanceSchemaUpdate = BalanceSchema.schemas.update


class Balance(BaseBackendModel[BalanceSchema, BalanceFilter, BalanceSchemaUpdate]):
    """Balance model with convenient methods"""

    _endpoint = "balances"

    def __init__(self, schema_obj: BalanceSchema, *, client: UAProjectClient):
        super().__init__(schema_obj, client=client)

    async def refresh_balance(self) -> None:
        """Refresh balance data from server"""
        await self.refresh()

    def __str__(self) -> str:
        return f"Balance(user_id={self.user_id}, amount={self.amount})"

    def __repr__(self) -> str:
        return f"<Balance user_id={self.user_id} amount={self.amount} identifier='{self.identifier}'>"