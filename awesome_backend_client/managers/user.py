"""User resource manager with custom methods"""

from typing import TYPE_CHECKING, Any, Literal

from uaproject_backend_schemas.models.user import (
    User as UserModel,
)

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import User

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.user import (
        UserFilter,
        UserSchemaCreate,
        UserSchemaUpdate,
    )
else:
    UserSchemaCreate = UserModel.schemas.create
    UserSchemaUpdate = UserModel.schemas.update
    UserFilter = UserModel.filter


class UserManager(
    BaseCRUDManager[UserModel, UserSchemaCreate, UserSchemaUpdate, UserFilter]
):
    """User resource manager with custom methods"""

    def __init__(self, client):
        super().__init__(client, "users", User)

    async def me(self) -> User:
        """Get current user"""
        return await self.get("me")

    async def search_by_nickname(
        self,
        nickname: str,
        *,
        skip: int = 0,
        limit: int = 100,
        search_mode: Literal["ilike", "similarity"] = "ilike",
        similarity_threshold: float = 0.3,
    ) -> list[User]:
        """Search users by minecraft nickname"""
        params = {
            "nickname": nickname,
            "skip": skip,
            "limit": limit,
            "search_mode": search_mode,
            "similarity_threshold": similarity_threshold,
        }
        data = await self.client.http.get("/users/search/nickname", params=params)
        return self._convert_to_models(data)

    async def set_minecraft_nickname(self, nickname: str) -> User:
        """Set minecraft nickname for current user"""
        data = await self.client.http.post(
            "/users/me/set-minecraft-nickname", data={"nickname": nickname}
        )
        return self._convert_to_model(data)

    async def get_permissions(self, user_id: int) -> dict[str, Any]:
        """Get user permissions"""
        return await self.client.http.get(f"/users/{user_id}/permissions")
