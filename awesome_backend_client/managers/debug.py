"""Debug endpoints manager"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from awesome_backend_client.client import UAProjectClient


class DebugManager:
    """Debug endpoints manager"""

    def __init__(self, client: "UAProjectClient"):
        self.client = client

    async def get_actions(self) -> list[dict[str, any]]:
        """Get debug actions"""
        return await self.client.http.get("/debug/actions")

    async def check_permission(self, permission: str) -> dict[str, any]:
        """Check permission"""
        return await self.client.http.get(f"/debug/auth/permission/{permission}")

    async def get_permissions(self) -> dict[str, any]:
        """Get permissions"""
        return await self.client.http.get("/debug/auth/permissions")

    async def refresh_auth(self) -> dict[str, any]:
        """Refresh auth"""
        return await self.client.http.post("/debug/auth/refresh")

    async def get_auth_status(self) -> dict[str, any]:
        """Get auth status"""
        return await self.client.http.get("/debug/auth/status")
