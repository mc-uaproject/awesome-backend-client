"""Simple balance manager with basic CRUD"""

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.balance import (
    Balance as BalanceModel,
)

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Balance

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.balance import (
        BalanceFilter,
        BalanceSchemaCreate,
        BalanceSchemaUpdate,
    )
else:
    BalanceFilter = BalanceModel.filter
    BalanceSchemaCreate = BalanceModel.schemas.create
    BalanceSchemaUpdate = BalanceModel.schemas.update


class BalanceManager(
    BaseCRUDManager[
        BalanceModel, BalanceSchemaCreate, BalanceSchemaUpdate, BalanceFilter
    ]
):
    """Simple balance manager with basic CRUD"""

    def __init__(self, client):
        super().__init__(client, "balances", Balance)
