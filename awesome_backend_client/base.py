"""Base CRUD manager for all API resources"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Literal, Self, TypeVar

from pydantic import BaseModel
from uaproject_backend_schemas.base import (
    CreateSchemaType,
    FilterSchemaType,
    ModelType,
    SortOrder,
    UpdateSchemaType,
)

if TYPE_CHECKING:
    from awesome_backend_client.client import UAProjectClient

BaseBackendModelType = TypeVar("BaseBackendModelType", bound="BaseBackendModel")


class BaseCRUDManager(
    Generic[BaseBackendModelType, CreateSchemaType, UpdateSchemaType, FilterSchemaType]
):
    """Universal CRUD manager that works with any resource"""

    def __init__(
        self,
        client: UAProjectClient,
        resource_name: str,
        model_class: type[BaseBackendModelType] | None = None,
    ):
        self.client = client
        self.resource_name = resource_name
        self.model_class = model_class
        self.endpoint = f"/{resource_name}"

    def _convert_input_data(self, data: dict[str, Any] | BaseModel) -> dict[str, Any]:
        """Convert Pydantic model or dict to dict for API request"""
        if isinstance(data, BaseModel):
            return data.model_dump(exclude_unset=True)
        if isinstance(data, dict):
            return data
        return data

    def _convert_to_model(
        self, data: dict[str, Any]
    ) -> BaseBackendModelType | dict[str, Any]:
        """Convert API response to model object if model_class is set"""
        if self.model_class and data:
            try:
                # Get resource name mapping for schema imports
                resource_mapping = {
                    "users": "user",
                    "roles": "role",
                    "applications": "application",
                    "balances": "balance",
                    "transactions": "transaction",
                    "punishments": "punishment",
                    "services": "service",
                    "files": "file",
                    "webhooks": "webhook",
                }

                schema_name = resource_mapping.get(
                    self.resource_name, self.resource_name.replace("-", "_")
                )

                # Import schema dynamically using the main model class name from schema
                schema_module = __import__(
                    f"uaproject_backend_schemas.models.{schema_name}",
                    fromlist=[schema_name.title()],
                )
                schema_class = getattr(schema_module, schema_name.title())
                schema_obj = schema_class.model_validate(data)
                return self.model_class(schema_obj, client=self.client)
            except (ImportError, AttributeError):
                # If model conversion fails, return raw data
                pass
        return data

    def _convert_to_models(
        self, data_list: list[dict[str, Any]]
    ) -> list[BaseBackendModelType | dict[str, Any]]:
        """Convert list of API responses to model objects"""
        return [self._convert_to_model(item) for item in data_list]

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort: SortOrder | None = None,
        order: str = "asc",
        **filters,
    ) -> list[BaseBackendModelType | dict[str, Any]]:
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
            return self._convert_to_models(data)
        raise TypeError(f"Expected list response, got {type(data)}")

    async def get(
        self, item_id: int | Literal["me"]
    ) -> BaseBackendModelType | dict[str, Any]:
        """Get resource by ID or 'me'"""
        data = await self.client.http.get(f"{self.endpoint}/{item_id}")
        if isinstance(data, dict):
            return self._convert_to_model(data)
        raise TypeError(f"Expected dict response, got {type(data)}")

    async def create(
        self, data: CreateSchemaType | dict[str, Any]
    ) -> BaseBackendModelType | dict[str, Any]:
        """Create new resource"""
        converted_data = self._convert_input_data(data)
        response_data = await self.client.http.post(self.endpoint, data=converted_data)
        if isinstance(response_data, dict):
            return self._convert_to_model(response_data)
        raise TypeError(f"Expected dict response, got {type(response_data)}")

    async def update(
        self, item_id: int | Literal["me"], data: UpdateSchemaType | dict[str, Any]
    ) -> BaseBackendModelType | dict[str, Any]:
        """Update resource by ID or 'me'"""
        converted_data = self._convert_input_data(data)
        response_data = await self.client.http.put(
            f"{self.endpoint}/{item_id}", data=converted_data
        )
        if isinstance(response_data, dict):
            return self._convert_to_model(response_data)
        raise TypeError(f"Expected dict response, got {type(response_data)}")

    async def delete(self, item_id: int | Literal["me"]) -> None:
        """Delete resource by ID or 'me'"""
        await self.client.http.delete(f"{self.endpoint}/{item_id}")

    def extend_with_custom_methods(self, **custom_methods):
        """Dynamically add custom methods to this manager"""
        for method_name, method_func in custom_methods.items():
            bound_method = method_func.__get__(self, self.__class__)
            setattr(self, method_name, bound_method)


class BaseBackendModel(Generic[ModelType, FilterSchemaType, UpdateSchemaType]):
    """
    Base model for all UAProject objects with universal CRUD operations

    Wraps Pydantic schema objects from uaproject-backend-schemas
    and adds convenience methods for API operations.
    """

    _endpoint: str  # Must be defined in subclasses

    def __init__(self, schema_obj: Any, *, client: UAProjectClient):
        self._schema = schema_obj
        self._client = client
        self._cache_key = None

    def __getattr__(self, name: str) -> Any:
        """Allow accessing schema fields as attributes"""
        if hasattr(self._schema, name):
            return getattr(self._schema, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to schema data"""
        if hasattr(self._schema, key):
            return getattr(self._schema, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in schema"""
        return hasattr(self._schema, key)

    def get_attr(self, key: str, default: Any = None) -> Any:
        """Get schema value with default (renamed to avoid conflict with get method)"""
        return getattr(self._schema, key, default)

    @property
    def schema(self) -> Any:
        """Get the underlying schema object"""
        return self._schema

    @property
    def dict(self) -> dict[str, Any]:
        """Get schema as dictionary"""
        return (
            self._schema.model_dump()
            if hasattr(self._schema, "model_dump")
            else dict(self._schema)
        )

    def _update_from_dict(self, data: dict[str, Any]) -> None:
        """Update internal schema from dict data"""
        if hasattr(self._schema, "model_validate"):
            self._schema = self._schema.__class__.model_validate(data)
        else:
            # Fallback for other schema types
            for key, value in data.items():
                if hasattr(self._schema, key):
                    setattr(self._schema, key, value)

    def _convert_filters(
        self, filters: dict[str, str | int | bool] | FilterSchemaType | None
    ) -> dict[str, Any] | None:
        """Convert filters to dict format"""
        if filters is None:
            return None
        if hasattr(filters, "model_dump"):
            return filters.model_dump(exclude_none=True)
        return filters

    def _convert_update_data(
        self, update_data: dict[str, str | int | bool] | UpdateSchemaType
    ) -> dict[str, Any]:
        """Convert update data to dict format"""
        if hasattr(update_data, "model_dump"):
            return update_data.model_dump(exclude_none=True)
        return update_data

    async def get(
        self,
        relation: str,
        filters: dict[str, str | int | bool] | FilterSchemaType | None = None,
        **params,
    ) -> ModelType | list[ModelType]:
        """Universal method to get related data"""
        converted_filters = self._convert_filters(filters)
        if converted_filters is None:
            converted_filters = {}
        # Add extra params (like limit, skip, etc.)
        converted_filters.update(params)

        # Try different endpoint patterns
        endpoints_to_try = [
            f"/{self._endpoint}/{self.id}/{relation}",
            f"/{relation}/{self._endpoint.rstrip('s')}/{self.id}",  # e.g. /punishments/user/1
            f"/{relation}",  # fallback to list with user_id filter
        ]

        for endpoint in endpoints_to_try:
            try:
                if endpoint == f"/{relation}":
                    # Add user_id filter for fallback
                    if converted_filters is None:
                        converted_filters = {}
                    converted_filters["user_id"] = self.id

                data = await self._client.http.get(endpoint, params=converted_filters)
                return self._convert_relation_data(data, relation)
            except Exception:
                continue

        raise ValueError(f"Could not find endpoint for relation '{relation}'")

    def _convert_relation_data(
        self, data: Any, relation: str
    ) -> ModelType | list[ModelType]:
        """Convert relation data to appropriate model objects"""
        # This is a simplified version - in real implementation we'd have
        # a mapping of relations to model classes
        if isinstance(data, list):
            return data  # Return as-is for now
        return data

    async def refresh(self) -> None:
        """Refresh object data from API"""
        fresh_data = await self._client.http.get(f"/{self._endpoint}/{self.id}")
        self._update_from_dict(fresh_data)

    async def edit(
        self, update_data: dict[str, str | int | bool] | UpdateSchemaType
    ) -> Self:
        """Edit object fields"""
        converted_data = self._convert_update_data(update_data)
        updated_data = await self._client.http.put(
            f"/{self._endpoint}/{self.id}", json=converted_data
        )
        self._update_from_dict(updated_data)
        return self

    async def delete(self) -> bool:
        """Delete object"""
        response = await self._client.http.delete(f"/{self._endpoint}/{self.id}")
        return response.status_code == 204
