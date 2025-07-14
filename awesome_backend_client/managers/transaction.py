"""Simple transaction manager with basic CRUD"""

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.transaction import (
    Transaction as TransactionSchema,
)

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
    TransactionSchemaCreate = TransactionSchema.schemas.create
    TransactionSchemaUpdate = TransactionSchema.schemas.update
    TransactionFilter = TransactionSchema.filter


class TransactionManager(
    BaseCRUDManager[
        Transaction, TransactionSchemaCreate, TransactionSchemaUpdate, TransactionFilter
    ]
):
    """Simple transaction manager with basic CRUD"""

    def __init__(self, client: "UAProjectClient"):
        from awesome_backend_client.models import Transaction

        super().__init__(client, "transactions", Transaction)
