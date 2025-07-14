"""Simple punishment manager with basic CRUD"""

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.punishment import (
    Punishment as PunishmentSchema,
)

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models.punishment import Punishment

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.punishment import (
        PunishmentFilter,
        PunishmentSchemaCreate,
        PunishmentSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    PunishmentFilter = PunishmentSchema.filter
    PunishmentSchemaCreate = PunishmentSchema.schemas.create
    PunishmentSchemaUpdate = PunishmentSchema.schemas.update


class PunishmentManager(
    BaseCRUDManager[
        Punishment, PunishmentSchemaCreate, PunishmentSchemaUpdate, PunishmentFilter
    ]
):
    """Simple punishment manager with basic CRUD"""

    def __init__(self, client: "UAProjectClient"):
        from awesome_backend_client.models import Punishment

        super().__init__(client, "punishments", Punishment)
