"""Role resource manager with custom methods"""

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.role import Role as RoleModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import Role

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.role import (
        RoleFilter,
        RoleSchemaCreate,
        RoleSchemaUpdate,
    )
else:
    RoleSchemaCreate = RoleModel.schemas.create
    RoleSchemaUpdate = RoleModel.schemas.update
    RoleFilter = RoleModel.filter


class RoleManager(
    BaseCRUDManager[
        Role,
        RoleSchemaCreate,
        RoleSchemaUpdate,
        RoleFilter,
    ]
):
    """Role resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "roles", Role)

    async def get_assignable(self) -> list[Role]:
        """Get roles that current user can assign to others"""
        data = await self.client.http.get("/roles/assignable")
        return self._convert_to_models(data)
