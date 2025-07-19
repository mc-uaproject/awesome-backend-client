"""User resource manager with custom methods"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from uaproject_backend_schemas.models.user import User as UserModel

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models import User

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.user import (
        UserFilter,
        UserSchemaCreate,
        UserSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    UserSchemaCreate = UserModel.schemas.create
    UserSchemaUpdate = UserModel.schemas.update
    UserFilter = UserModel.filter


class UserManager(
    BaseCRUDManager[User, UserSchemaCreate, UserSchemaUpdate, UserFilter]
):
    """User resource manager with custom methods"""

    def __init__(self, client: UAProjectClient) -> None:
        super().__init__(client, "users", User)

    async def me(self) -> User:
        """Get current user"""
        result = await self.get("me")
        if isinstance(result, User):
            return result
        raise TypeError(f"Expected User, got {type(result)}")

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
        if isinstance(data, list):
            results = self._convert_to_models(data)
            # Filter out non-User objects
            return [item for item in results if isinstance(item, User)]
        raise TypeError(f"Expected list response, got {type(data)}")

    async def set_minecraft_nickname(self, nickname: str) -> User:
        """Set minecraft nickname for current user"""
        data = await self.client.http.post(
            "/users/me/set-minecraft-nickname", json={"nickname": nickname}
        )
        if isinstance(data, dict):
            result = self._convert_to_model(data)
            if isinstance(result, User):
                return result
            raise TypeError(f"Expected User, got {type(result)}")
        raise TypeError(f"Expected dict response, got {type(data)}")

    async def get_permissions(self, user_id: int) -> dict[str, Any]:
        """Get user permissions"""
        data = await self.client.http.get(f"/users/{user_id}/permissions")
        if isinstance(data, dict):
            return data
        raise TypeError(f"Expected dict response, got {type(data)}")
