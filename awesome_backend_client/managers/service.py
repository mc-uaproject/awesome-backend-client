"""Simple service manager with basic CRUD"""

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.service import (
    Service as ServiceSchema,
)

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
    ServiceFilter = ServiceSchema.filter
    ServiceSchemaCreate = ServiceSchema.schemas.create
    ServiceSchemaUpdate = ServiceSchema.schemas.update


class ServiceManager(
    BaseCRUDManager[Service, ServiceSchemaCreate, ServiceSchemaUpdate, ServiceFilter]
):
    """Simple service manager with basic CRUD"""

    def __init__(self, client: "UAProjectClient"):
        from awesome_backend_client.models import Service

        super().__init__(client, "services", Service)
