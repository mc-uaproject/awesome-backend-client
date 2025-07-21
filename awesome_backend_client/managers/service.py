"""Service resource manager"""

from __future__ import annotations

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.service import Service as ServiceModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Service

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.service import (
        ServiceFilter,
        ServiceSchemaCreate,
        ServiceSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    ServiceSchemaCreate = ServiceModel.schemas.create
    ServiceSchemaUpdate = ServiceModel.schemas.update
    ServiceFilter = ServiceModel.filter


class ServiceManager(
    BaseCRUDManager[Service, ServiceSchemaCreate, ServiceSchemaUpdate, ServiceFilter]
):
    """Service resource manager"""

    def __init__(self, client: UAProjectClient) -> None:
        super().__init__(client, "services", Service)
