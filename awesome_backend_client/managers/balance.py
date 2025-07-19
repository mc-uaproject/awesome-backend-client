"""Balance resource manager with custom methods"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.balance import Balance as BalanceModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Balance

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.balance import (
        BalanceFilter,
        BalanceSchemaCreate,
        BalanceSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    BalanceSchemaCreate = BalanceModel.schemas.create
    BalanceSchemaUpdate = BalanceModel.schemas.update
    BalanceFilter = BalanceModel.filter


class BalanceManager(
    BaseCRUDManager[Balance, BalanceSchemaCreate, BalanceSchemaUpdate, BalanceFilter]
):
    """Balance resource manager with custom methods"""

    def __init__(self, client: UAProjectClient) -> None:
        super().__init__(client, "balances", Balance)

    async def get_by_user_id(self, user_id: int, *, _raise: bool = True) -> Balance | None:
        """Get balance by user ID (assumes user_id is unique for balances)"""
        result = await self.get_by(_raise=_raise, user_id=user_id)
        if result is None:
            return None
        if isinstance(result, Balance):
            return result
        raise TypeError(f"Expected Balance, got {type(result)}")

    async def get_many(
        self,
        *,
        filters: dict[str, str | int | bool] | None = None,
        skip: int = 0,
        limit: int = 100,
        **extra_filters: str | int | bool,
    ) -> list[Balance]:
        """Get multiple balances with filters"""
        all_filters = {**(filters or {}), **extra_filters}
        results = await self.list(skip=skip, limit=limit, **all_filters)
        balances = []
        for result in results:
            if isinstance(result, Balance):
                balances.append(result)
            else:
                raise TypeError(f"Expected Balance, got {type(result)}")
        return balances