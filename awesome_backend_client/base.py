"""Base CRUD manager for all API resources"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, Self, TypeVar

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

BaseBackendModelType = TypeVar(
    "BaseBackendModelType", bound="BaseBackendModel[Any, Any, Any]"
)


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
            return data.model_dump(exclude_unset=True, mode="json")
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
                from types import ModuleType
                from typing import cast

                schema_module = cast(
                    ModuleType,
                    __import__(
                        f"uaproject_backend_schemas.models.{schema_name}",
                        fromlist=[schema_name.title()],
                    ),
                )
                schema_class = cast(
                    type[BaseModel], getattr(schema_module, schema_name.title())
                )
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
        _raise: bool = True,
        **filters: str | int | bool,
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
            results = self._convert_to_models(data)
            if not results and not _raise:
                return []
            return results
        msg = f"Expected list response, got {type(data)}"
        raise TypeError(msg)

    async def get(
        self, item_id: int | Literal["me"], *, _raise: bool = True
    ) -> BaseBackendModelType | dict[str, Any] | None:
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
    ) -> BaseBackendModelType | dict[str, Any]:
        """Create new resource"""
        converted_data = self._convert_input_data(data)
        response_data = await self.client.http.post(self.endpoint, data=converted_data)
        if isinstance(response_data, dict):
            return self._convert_to_model(response_data)
        msg = f"Expected dict response, got {type(response_data)}"
        raise TypeError(msg)

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
        msg = f"Expected dict response, got {type(response_data)}"
        raise TypeError(msg)

    async def delete(self, item_id: int | Literal["me"]) -> None:
        """Delete resource by ID or 'me'"""
        await self.client.http.delete(f"{self.endpoint}/{item_id}")

    async def get_by(
        self, *, _raise: bool = True, **filters: str | int | bool
    ) -> BaseBackendModelType | dict[str, Any] | None:
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


class BaseBackendModel(Generic[ModelType, FilterSchemaType, UpdateSchemaType]):
    """
    Base model for all UAProject objects with universal CRUD operations

    Wraps Pydantic schema objects from uaproject-backend-schemas
    and adds convenience methods for API operations.
    """

    _endpoint: str  # Must be defined in subclasses

    def __init__(self, schema_obj: BaseModel, *, client: UAProjectClient):
        self._schema = schema_obj
        self._client = client
        self._cache_key = None

    def __getattr__(self, name: str) -> Any:
        """Allow accessing schema fields as attributes"""
        if hasattr(self._schema, name):
            return getattr(self._schema, name)
        msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
        raise AttributeError(msg)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to schema data"""
        if hasattr(self._schema, key):
            return getattr(self._schema, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in schema"""
        return hasattr(self._schema, key)

    def get_attr(self, key: str, default: object = None) -> object:
        """Get schema value with default (renamed to avoid conflict with get method)"""
        return getattr(self._schema, key, default)

    @property
    def schema(self) -> BaseModel:
        """Get the underlying schema object"""
        return self._schema

    def to_dict(self) -> dict[str, Any]:
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
        self, filters: dict[str, Any] | FilterSchemaType | None
    ) -> dict[str, Any] | None:
        """Convert filters to dict format"""
        if filters is None:
            return None
        if isinstance(filters, dict):
            return filters
        if hasattr(filters, "model_dump"):
            return filters.model_dump(exclude_none=True)
        return {}

    def _convert_update_data(
        self, update_data: dict[str, Any] | UpdateSchemaType
    ) -> dict[str, Any]:
        """Convert update data to dict format"""
        if isinstance(update_data, dict):
            return update_data
        if hasattr(update_data, "model_dump"):
            return update_data.model_dump(exclude_none=True)
        return {}

    async def get(
        self,
        relation: str,
        filters: dict[str, Any] | FilterSchemaType | None = None,
        **params: str | int | bool,
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
                    if not converted_filters:
                        converted_filters = {}
                    converted_filters["user_id"] = self.id

                data = await self._client.http.get(endpoint, params=converted_filters)
                return self._convert_relation_data(data, relation)
            except Exception:
                continue

        msg = f"Could not find endpoint for relation '{relation}'"
        raise ValueError(msg)

    def _convert_relation_data(
        self, data: Any, relation: str
    ) -> ModelType | list[ModelType]:
        """Convert relation data to appropriate model objects"""
        # This is a simplified version - in real implementation we'd have
        # a mapping of relations to model classes
        if isinstance(data, list):
            return data  # type: ignore[return-value]
        return data  # type: ignore[return-value,no-any-return]

    async def refresh(self) -> None:
        """Refresh object data from API"""
        fresh_data = await self._client.http.get(f"/{self._endpoint}/{self.id}")
        if isinstance(fresh_data, dict):
            self._update_from_dict(fresh_data)

    async def edit(self, update_data: dict[str, Any] | UpdateSchemaType) -> Self:
        """Edit object fields"""
        converted_data = self._convert_update_data(update_data)
        updated_data = await self._client.http.put(
            f"/{self._endpoint}/{self.id}", json=converted_data
        )
        if isinstance(updated_data, dict):
            self._update_from_dict(updated_data)
        return self

    async def delete(self) -> bool:
        """Delete object"""
        response = await self._client.http.delete(f"/{self._endpoint}/{self.id}")
        # HTTP DELETE typically returns 204 for successful deletion
        # Since we don't have access to the actual response object,
        # we assume success if no exception was raised
        return True
