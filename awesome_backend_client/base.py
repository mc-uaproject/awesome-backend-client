"""Base CRUD manager for all API resources"""

from typing import TYPE_CHECKING, Any, Generic, Literal, Optional

from uaproject_backend_schemas import (
    CreateSchemaType,
    FilterSchemaType,
    ModelType,
    SortOrder,
    UpdateSchemaType,
)

if TYPE_CHECKING:
    from awesome_backend_client.client import UAProjectClient


class BaseCRUDManager(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, FilterSchemaType]
):
    """Universal CRUD manager that works with any resource"""

    def __init__(
        self,
        client: "UAProjectClient",
        resource_name: str,
        model_class: Optional["BaseBackendModel"] = None,
    ):
        self.client = client
        self.resource_name = resource_name
        self.model_class = model_class
        self.endpoint = f"/{resource_name}"

    def _convert_input_data(self, data: dict[str, Any] | Any) -> dict[str, Any]:
        """Convert Pydantic model or dict to dict for API request"""
        if hasattr(data, "model_dump"):
            return data.model_dump(exclude_unset=True)
        elif hasattr(data, "dict"):
            return data.dict(exclude_unset=True)
        return data

    def _convert_to_model(self, data: dict[str, Any]) -> ModelType | dict[str, Any]:
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
    ) -> list[ModelType | dict[str, Any]]:
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
    ) -> list[ModelType | dict[str, Any]]:
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
        return self._convert_to_models(data)

    async def get(self, item_id: int | Literal["me"]) -> ModelType | dict[str, Any]:
        """Get resource by ID or 'me'"""
        data = await self.client.http.get(f"{self.endpoint}/{item_id}")
        return self._convert_to_model(data)

    async def create(
        self, data: CreateSchemaType | dict[str, Any]
    ) -> ModelType | dict[str, Any]:
        """Create new resource"""
        converted_data = self._convert_input_data(data)
        response_data = await self.client.http.post(self.endpoint, data=converted_data)
        return self._convert_to_model(response_data)

    async def update(
        self, item_id: int | Literal["me"], data: UpdateSchemaType | dict[str, Any]
    ) -> ModelType | dict[str, Any]:
        """Update resource by ID or 'me'"""
        converted_data = self._convert_input_data(data)
        response_data = await self.client.http.put(
            f"{self.endpoint}/{item_id}", data=converted_data
        )
        return self._convert_to_model(response_data)

    async def delete(self, item_id: int | Literal["me"]) -> None:
        """Delete resource by ID or 'me'"""
        await self.client.http.delete(f"{self.endpoint}/{item_id}")

    def extend_with_custom_methods(self, **custom_methods):
        """Dynamically add custom methods to this manager"""
        for method_name, method_func in custom_methods.items():
            bound_method = method_func.__get__(self, self.__class__)
            setattr(self, method_name, bound_method)


class BaseBackendModel:
    """
    Base model for all UAProject objects

    Wraps Pydantic schema objects from uaproject-backend-schemas
    and adds convenience methods for API operations.
    """

    def __init__(self, schema_obj: Any, *, client: "UAProjectClient"):
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

    def get(self, key: str, default: Any = None) -> Any:
        """Get schema value with default"""
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

    async def refresh(self):
        """Refresh object data from API - to be implemented by subclasses"""
        if hasattr(self, "id") and self.id:
            # This will be implemented by subclasses
            pass

    async def edit(self, **fields):
        """Edit object fields - to be implemented by subclasses"""
        raise NotImplementedError(
            f"edit() method not implemented for {self.__class__.__name__}"
        )

    async def delete(self) -> bool:
        """Delete object - to be implemented by subclasses"""
        raise NotImplementedError(
            f"delete() method not implemented for {self.__class__.__name__}"
        )
