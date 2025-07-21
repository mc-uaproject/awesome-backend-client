"""Service model with methods for service operations"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from uaproject_backend_schemas.models.schemas.transaction import TransactionType
from uaproject_backend_schemas.models.service import Service as ServiceModel

from awesome_backend_client.mixins import ClientModelMixin

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.service import (
        ServiceSchemaCreate,
        ServiceSchemaResponse,
        ServiceSchemaUpdate,
    )

    from awesome_backend_client.models.transaction import Transaction
    from awesome_backend_client.models.user import User
else:
    ServiceSchemaCreate = ServiceModel.schemas.create
    ServiceSchemaUpdate = ServiceModel.schemas.update
    ServiceSchemaResponse = ServiceModel.schemas.response

logger = logging.getLogger(__name__)


class Service(
    ServiceSchemaResponse, ClientModelMixin[ServiceSchemaCreate, ServiceSchemaUpdate]
):
    """
    Service model with direct inheritance from ServiceResponse schema.

    All schema fields are accessible directly (id, name, price, type, etc.)
    with full typing support. Provides async methods for service operations.
    """

    _endpoint: ClassVar[str] = "services"

    @property
    def is_subscription(self) -> bool:
        """Check if service is a subscription type"""
        return hasattr(self, "type") and self.type == "subscription"

    @property
    def is_available(self) -> bool:
        """Check if service is available for purchase"""
        return bool(self.is_active)

    async def purchase(
        self, recipient_id: int | None = None, description: str | None = None
    ) -> Transaction:
        """Purchase this service"""
        if not self.is_available:
            raise ValueError(f"Service {self.id} is not available for purchase")

        if recipient_id is None:
            if not hasattr(self._client, "impersonate_user_id"):
                raise ValueError("recipient_id is required when not impersonating")
            recipient_id = self._client.impersonate_user_id

        transaction_data = {
            "recipient_id": recipient_id,
            "service_id": self.id,
            "type": TransactionType.PURCHASE,
            "description": description or f"Purchase of {self.name}",
        }

        return await self._client.transactions.create(transaction_data)

    async def get_purchases(
        self, limit: int = 100, **filters: Any
    ) -> list[Transaction]:
        """Get all purchases of this service"""
        filters["service_id"] = self.id
        filters["type"] = TransactionType.PURCHASE
        return await self._client.transactions.list(limit=limit, **filters)

    async def get_purchasers(self, limit: int = 100) -> list[User]:
        """Get users who purchased this service"""
        transactions = await self.get_purchases(limit=limit)
        user_ids = {t.recipient_id for t in transactions if t.recipient_id}
        users = []
        for user_id in user_ids:
            user = await self._client.users.get(user_id, _raise=False)
            if user:
                users.append(user)
        return users
