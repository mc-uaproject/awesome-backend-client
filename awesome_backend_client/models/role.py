"""Role model with methods for role operations"""

import logging
from typing import TYPE_CHECKING

from uaproject_backend_schemas.models import (
    Role as RoleSchema,
)

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.role import RoleSchemaResponse

    from awesome_backend_client.client import UAProjectClient
else:
    RoleSchemaResponse = RoleSchema.schemas.response

logger = logging.getLogger(__name__)


class Role(BaseBackendModel, RoleSchemaResponse):
    """
    Role model with methods for role operations
    """

    def __init__(self, role_schema: RoleSchemaResponse, *, client: "UAProjectClient"):
        super().__init__(role_schema, client=client)

    async def refresh(self):
        """Refresh role data from API"""
        try:
            fresh_data = await self._client.roles.get(self.id)
            self._schema = RoleSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh role {self.id}: {e}")

    async def edit(self, **fields) -> "Role":
        """Edit role fields"""
        updated_data = await self._client.roles.update(self.id, fields)
        self._schema = RoleSchema.model_validate(updated_data)
        return self

    async def add_permission(self, permission: str) -> "Role":
        """Add permission to role"""
        current_permissions = getattr(self._schema, "permissions", []) or []
        if permission not in current_permissions:
            current_permissions.append(permission)
            await self.edit(permissions=current_permissions)
        return self

    async def remove_permission(self, permission: str) -> "Role":
        """Remove permission from role"""
        current_permissions = getattr(self._schema, "permissions", []) or []
        if permission in current_permissions:
            current_permissions.remove(permission)
            await self.edit(permissions=current_permissions)
        return self

    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        permissions = getattr(self._schema, "permissions", []) or []
        return permission in permissions

    def __str__(self) -> str:
        return f"Role(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        return f"<Role id={self.id} name='{self.name}'>"
