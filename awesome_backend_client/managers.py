"""Universal CRUD managers for all API resources"""

from typing import Any, Generic, Literal, Optional, TypeVar, Union

T = TypeVar("T")


class BaseCRUDManager(Generic[T]):
    """Universal CRUD manager that works with any resource"""

    def __init__(self, client, resource_name: str, model_class=None):
        self.client = client
        self.resource_name = resource_name
        self.model_class = model_class
        self.endpoint = f"/{resource_name}"

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[str] = None,
        order: str = "asc",
        **filters,
    ) -> list[dict[str, Any]]:
        """List resources with optional filtering and sorting"""
        params = {
            "skip": skip,
            "limit": limit,
            "order": order,
            **filters,
        }
        if sort:
            params["sort"] = sort

        return await self.client.http.get(self.endpoint, params=params)

    async def get(self, item_id: Union[int, str]) -> dict[str, Any]:
        """Get resource by ID or 'me'"""
        return await self.client.http.get(f"{self.endpoint}/{item_id}")

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create new resource"""
        return await self.client.http.post(self.endpoint, data=data)

    async def update(
        self, item_id: Union[int, str], data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update resource by ID or 'me'"""
        return await self.client.http.put(f"{self.endpoint}/{item_id}", data=data)

    async def delete(self, item_id: Union[int, str]) -> None:
        """Delete resource by ID or 'me'"""
        await self.client.http.delete(f"{self.endpoint}/{item_id}")

    def extend_with_custom_methods(self, **custom_methods):
        """Dynamically add custom methods to this manager"""
        for method_name, method_func in custom_methods.items():
            # Bind the method to this instance
            bound_method = method_func.__get__(self, self.__class__)
            setattr(self, method_name, bound_method)


class UserManager(BaseCRUDManager):
    """User resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "users")

    async def me(self) -> dict[str, Any]:
        """Get current user"""
        return await self.client.http.get("/users/me")

    async def search_by_nickname(
        self,
        nickname: str,
        *,
        skip: int = 0,
        limit: int = 100,
        search_mode: Literal["ilike", "similarity"] = "ilike",
        similarity_threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Search users by minecraft nickname"""
        params = {
            "nickname": nickname,
            "skip": skip,
            "limit": limit,
            "search_mode": search_mode,
            "similarity_threshold": similarity_threshold,
        }
        return await self.client.http.get("/users/search/nickname", params=params)

    async def set_minecraft_nickname(self, nickname: str) -> dict[str, Any]:
        """Set minecraft nickname for current user"""
        return await self.client.http.post(
            "/users/me/set-minecraft-nickname", data={"nickname": nickname}
        )

    async def get_permissions(self, user_id: int) -> dict[str, Any]:
        """Get user permissions"""
        return await self.client.http.get(f"/users/{user_id}/permissions")


class RoleManager(BaseCRUDManager):
    """Role resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "roles")

    async def get_assignable(self) -> list[dict[str, Any]]:
        """Get roles that current user can assign to others"""
        return await self.client.http.get("/roles/assignable")


class ApplicationManager(BaseCRUDManager):
    """Application resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "applications")

    async def get_base(self) -> dict[str, Any]:
        """Get base application template"""
        return await self.client.http.get("/applications/base")

    async def get_evervault(self) -> dict[str, Any]:
        """Get evervault application"""
        return await self.client.http.get("/applications/evervault")

    async def get_v2(self) -> list[dict[str, Any]]:
        """Get v2 applications"""
        return await self.client.http.get("/applications/v2")

    async def get_count(self, **filters) -> dict[str, Any]:
        """Get application count with filters"""
        return await self.client.http.get("/applications/list/count", params=filters)

    async def search(self, **params) -> list[dict[str, Any]]:
        """Search applications"""
        return await self.client.http.get("/applications/list/search", params=params)

    async def submit_section(
        self, application_id: int, section_name: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Submit application section"""
        return await self.client.http.post(
            f"/applications/{application_id}/section/{section_name}/submit",
            data=data,
        )


class ApplicationSectionManager(BaseCRUDManager):
    """Application section resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "application-sections")

    async def get_by_application(self, application_id: int) -> list[dict[str, Any]]:
        """Get sections for application"""
        return await self.client.http.get(
            f"/application-sections/application/{application_id}"
        )

    async def get_by_application_and_server(
        self, application_id: int, server_type: str
    ) -> list[dict[str, Any]]:
        """Get sections for application and server type"""
        return await self.client.http.get(
            f"/application-sections/application/{application_id}/server/{server_type}"
        )


class ClaimManager(BaseCRUDManager):
    """Claim resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "claims")

    async def get_by_claimant(self, user_id: int) -> list[dict[str, Any]]:
        """Get claims where user is claimant"""
        return await self.client.http.get(f"/claims/claimant/{user_id}")

    async def get_by_defendant(self, user_id: int) -> list[dict[str, Any]]:
        """Get claims where user is defendant"""
        return await self.client.http.get(f"/claims/defendant/{user_id}")

    async def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get claims by status"""
        return await self.client.http.get(f"/claims/status/{status}")

    async def get_judging(self, judging_id: int) -> dict[str, Any]:
        """Get claim judging"""
        return await self.client.http.get(f"/claims/judging/{judging_id}")


class TicketManager(BaseCRUDManager):
    """Ticket resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "tickets")

    async def get_assignments(self, **filters) -> list[dict[str, Any]]:
        """Get ticket assignments"""
        return await self.client.http.get("/ticket-assignments", params=filters)

    async def create_assignment(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create ticket assignment"""
        return await self.client.http.post("/ticket-assignments", data=data)

    async def update_assignment(
        self, assignment_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update ticket assignment"""
        return await self.client.http.put(
            f"/ticket-assignments/{assignment_id}", data=data
        )

    async def delete_assignment(self, assignment_id: int) -> None:
        """Delete ticket assignment"""
        await self.client.http.delete(f"/ticket-assignments/{assignment_id}")


class WebhookManager(BaseCRUDManager):
    """Advanced webhook resource manager with registration and management"""

    def __init__(self, client):
        super().__init__(client, "webhooks")

    async def execute(self, webhook_id: int, data: dict[str, Any]) -> None:
        """Execute webhook manually"""
        await self.client.http.post(f"/webhooks/{webhook_id}/execute", data=data)

    async def test(self, webhook_id: int) -> dict[str, Any]:
        """Test webhook endpoint connectivity"""
        return await self.client.http.post(f"/webhooks/{webhook_id}/test")

    async def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get webhooks by status"""
        return await self.list(status=status)

    async def get_by_endpoint(self, endpoint: str) -> list[dict[str, Any]]:
        """Get webhooks by endpoint URL"""
        return await self.list(endpoint=endpoint)

    async def activate(self, webhook_id: int) -> dict[str, Any]:
        """Activate webhook"""
        return await self.update(webhook_id, {"status": "active"})

    async def deactivate(self, webhook_id: int) -> dict[str, Any]:
        """Deactivate webhook"""
        return await self.update(webhook_id, {"status": "inactive"})

    async def pause(self, webhook_id: int) -> dict[str, Any]:
        """Pause webhook"""
        return await self.update(webhook_id, {"status": "paused"})

    async def bulk_activate(self, webhook_ids: list[int]) -> list[dict[str, Any]]:
        """Activate multiple webhooks"""
        results = []
        for webhook_id in webhook_ids:
            result = await self.activate(webhook_id)
            results.append(result)
        return results

    async def bulk_deactivate(self, webhook_ids: list[int]) -> list[dict[str, Any]]:
        """Deactivate multiple webhooks"""
        results = []
        for webhook_id in webhook_ids:
            result = await self.deactivate(webhook_id)
            results.append(result)
        return results

    async def get_logs(
        self,
        webhook_id: Optional[int] = None,
        limit: int = 100,
        status: Optional[str] = None,
        **filters,
    ) -> list[dict[str, Any]]:
        """Get webhook execution logs"""
        params = {"limit": limit, **filters}
        if webhook_id:
            params["webhook_id"] = webhook_id
        if status:
            params["status"] = status

        # Use webhook-logs endpoint
        return await self.client.http.get("/webhook-logs", params=params)

    async def get_failed_logs(
        self, webhook_id: Optional[int] = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get failed webhook execution logs"""
        return await self.get_logs(webhook_id=webhook_id, status="failed", limit=limit)

    async def retry_failed(self, webhook_id: int, log_id: int) -> dict[str, Any]:
        """Retry failed webhook execution"""
        return await self.client.http.post(f"/webhooks/{webhook_id}/retry/{log_id}")


class DebugManager:
    """Debug endpoints manager"""

    def __init__(self, client):
        self.client = client

    async def get_actions(self) -> list[dict[str, Any]]:
        """Get debug actions"""
        return await self.client.http.get("/debug/actions")

    async def check_permission(self, permission: str) -> dict[str, Any]:
        """Check permission"""
        return await self.client.http.get(f"/debug/auth/permission/{permission}")

    async def get_permissions(self) -> dict[str, Any]:
        """Get permissions"""
        return await self.client.http.get("/debug/auth/permissions")

    async def refresh_auth(self) -> dict[str, Any]:
        """Refresh auth"""
        return await self.client.http.post("/debug/auth/refresh")

    async def get_auth_status(self) -> dict[str, Any]:
        """Get auth status"""
        return await self.client.http.get("/debug/auth/status")


# Auto-generated managers for all other resources (without custom methods)
# These will automatically work with the standard CRUD operations


# Simple managers that only need basic CRUD
def BalanceManager(client):
    return BaseCRUDManager(client, "balances")


def TransactionManager(client):
    return BaseCRUDManager(client, "transactions")


def PunishmentManager(client):
    return BaseCRUDManager(client, "punishments")


def PunishmentConfigManager(client):
    return BaseCRUDManager(client, "punishment-configs")


def ServiceManager(client):
    return BaseCRUDManager(client, "services")


def FileManager(client):
    return BaseCRUDManager(client, "files")


def NewsManager(client):
    return BaseCRUDManager(client, "news")


def JudgingManager(client):
    return BaseCRUDManager(client, "judgings")


def PurchasedItemManager(client):
    return BaseCRUDManager(client, "purchased-items")


def TicketMessageManager(client):
    return BaseCRUDManager(client, "ticket-messages")


def TokenManager(client):
    return BaseCRUDManager(client, "tokens")


def WebhookLogManager(client):
    return BaseCRUDManager(client, "webhook-logs")
