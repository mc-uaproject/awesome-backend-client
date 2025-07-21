"""Base CRUD manager for all API resources"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from pydantic import BaseModel
from uaproject_backend_schemas.base import (
    CreateSchemaType,
    FilterSchemaType,
    SortOrder,
    UpdateSchemaType,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from awesome_backend_client.client import UAProjectClient
    from awesome_backend_client.mixins import ClientModelProtocol

ClientModelMixinType = TypeVar(
    "ClientModelMixinType", bound="ClientModelProtocol"
)


class BaseCRUDManager(
    Generic[ClientModelMixinType, CreateSchemaType, UpdateSchemaType, FilterSchemaType]
):
    """Universal CRUD manager that works with any resource"""

    def __init__(
        self,
        client: UAProjectClient,
        resource_name: str,
        model_class: type[ClientModelMixinType] | None = None,
    ):
        self.client = client
        self.resource_name = resource_name
        self.model_class = model_class
        self.endpoint = f"/{resource_name}"

    def _convert_input_data(self, data: dict[str, Any] | BaseModel) -> dict[str, Any]:
        """Convert Pydantic model or dict to dict for API request"""
        if isinstance(data, BaseModel):
            return data.model_dump(exclude_unset=True, mode="json")
        return data

    def _convert_to_model(self, data: dict[str, Any]) -> ClientModelMixinType:
        """Convert API response to model object if model_class is set"""
        if not self.model_class:
            raise ValueError("model_class is not set")

        if not data:
            raise ValueError("data is empty")

        return self.model_class(data, client=self.client)

    def _convert_to_models(
        self, data_list: list[dict[str, Any]]
    ) -> list[ClientModelMixinType]:
        """Convert list of API responses to model objects"""
        return [self._convert_to_model(item) for item in data_list]

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort: SortOrder | None = None,
        order: str = "asc",
        _raise: bool = True,
        **filters: Any,
    ) -> list[ClientModelMixinType]:
        """List resources with optional filtering and sorting"""
        params = {
            "skip": skip,
            "limit": limit,
            "order": order,
            **filters,
        }
        if sort:
            params["sort"] = sort

        data = await self.client.http.get(self.endpoint, params=params)
        if isinstance(data, list):
            results = self._convert_to_models(data)
            if not results and not _raise:
                return []
            return results
        msg = f"Expected list response, got {type(data)}"
        raise TypeError(msg)

    async def get(
        self, item_id: int | Literal["me"], *, _raise: bool = True
    ) -> ClientModelMixinType | None:
        """Get resource by ID or 'me'"""
        try:
            data = await self.client.http.get(f"{self.endpoint}/{item_id}")
            if isinstance(data, dict):
                return self._convert_to_model(data)
            msg = f"Expected dict response, got {type(data)}"
            raise TypeError(msg)
        except Exception as e:
            # Check if it's a 404 or similar "not found" error
            if "404" in str(e) or "not found" in str(e).lower():
                if _raise:
                    raise
                return None
            # Re-raise other errors (network, auth, etc.)
            raise

    async def create(
        self, data: CreateSchemaType | dict[str, Any]
    ) -> ClientModelMixinType:
        """Create new resource"""
        converted_data = self._convert_input_data(data)
        response_data = await self.client.http.post(self.endpoint, data=converted_data)
        if isinstance(response_data, dict):
            return self._convert_to_model(response_data)
        msg = f"Expected dict response, got {type(response_data)}"
        raise TypeError(msg)

    async def update(
        self, item_id: int | Literal["me"], data: UpdateSchemaType | dict[str, Any]
    ) -> ClientModelMixinType:
        """Update resource by ID or 'me'"""
        converted_data = self._convert_input_data(data)
        response_data = await self.client.http.put(
            f"{self.endpoint}/{item_id}", data=converted_data
        )
        if isinstance(response_data, dict):
            return self._convert_to_model(response_data)
        msg = f"Expected dict response, got {type(response_data)}"
        raise TypeError(msg)

    async def delete(self, item_id: int | Literal["me"]) -> None:
        """Delete resource by ID or 'me'"""
        await self.client.http.delete(f"{self.endpoint}/{item_id}")

    async def get_by(
        self, *, _raise: bool = True, **filters: str | int | bool
    ) -> ClientModelMixinType | None:
        """Get single resource by unique field(s). Raises error if not unique or not found."""
        results = await self.list(limit=2, _raise=_raise, **filters)

        if not results:
            return None

        if len(results) > 1:
            filter_str = ", ".join(f"{k}={v}" for k, v in filters.items())
            msg = f"Multiple {self.resource_name} found with {filter_str}, expected unique result"
            raise ValueError(msg)

        return results[0]

    def extend_with_custom_methods(self, **custom_methods: Callable[..., Any]) -> None:
        """Dynamically add custom methods to this manager"""
        for method_name, method_func in custom_methods.items():
            bound_method = method_func.__get__(self, self.__class__)
            setattr(self, method_name, bound_method)
