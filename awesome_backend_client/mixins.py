"""Mixins for client models"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Protocol,
    runtime_checkable,
)

if TYPE_CHECKING:
    from awesome_backend_client.client import UAProjectClient

from uaproject_backend_schemas.base import CreateSchemaType, UpdateSchemaType


@runtime_checkable
class ClientModelProtocol(Protocol):
    """Protocol for client model requirements"""

    id: int
    _endpoint: ClassVar[str]
    _client: UAProjectClient

    def model_dump(self, *, mode: str = "python", **kwargs: Any) -> dict[str, Any]: ...
    def _update_from_dict(self, data: dict[str, Any]) -> None: ...
    def _convert_update_data(
        self, update_data: dict[str, Any] | Any
    ) -> dict[str, Any]: ...


class ClientModelMixin(Generic[CreateSchemaType, UpdateSchemaType]):
    """Mixin providing API methods for client models"""

    _endpoint: ClassVar[str]
    _client: UAProjectClient

    def __init_subclass__(cls: type, **kwargs: Any) -> None:
        """Configure the subclass when it's created"""
        # Call parent __init_subclass__ if it exists
        for parent in cls.__mro__[1:]:
            if hasattr(parent, "__init_subclass__"):
                parent.__init_subclass__(**kwargs)
                break

        # Add model_config if not present
        if not hasattr(cls, "model_config"):
            cls.model_config = {}  # type: ignore

        # Allow arbitrary attributes to bypass Pydantic validation
        if isinstance(cls.model_config, dict):  # type: ignore
            cls.model_config["arbitrary_types_allowed"] = True  # type: ignore

        # Override __init__ to handle client injection
        original_init = cls.__init__  # type: ignore

        def new_init(
            self: Any, data: dict[str, Any], *, client: UAProjectClient
        ) -> None:
            # Initialize Pydantic model
            original_init(self, **data)
            # Store client reference
            object.__setattr__(self, "_client", client)

        cls.__init__ = new_init  # type: ignore

        cls.__str__ = ClientModelMixin.__str__  # type: ignore
        cls.__repr__ = ClientModelMixin.__repr__  # type: ignore

    def _update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model fields from dict data"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _convert_update_data(
        self, update_data: dict[str, Any] | UpdateSchemaType
    ) -> dict[str, Any]:
        """Convert update data to dict format"""
        if isinstance(update_data, dict):
            return update_data

        # Check if it's a Pydantic model using Protocol
        if isinstance(update_data, ClientModelProtocol):
            return update_data.model_dump(exclude_none=True, mode="json")

        # Fallback for other types
        return {}

    def to_dict(self: ClientModelProtocol) -> dict[str, Any]:
        """Convert model to dictionary"""
        return self.model_dump(mode="json")

    async def refresh(self: ClientModelProtocol) -> ClientModelProtocol:
        """Refresh model data from API"""
        fresh_data = await self._client.http.get(f"/{self._endpoint}/{self.id}")
        if isinstance(fresh_data, dict):
            self._update_from_dict(fresh_data)
        return self

    async def update(
        self: ClientModelProtocol, data: UpdateSchemaType | dict[str, Any]
    ) -> ClientModelProtocol:
        """Update model via API"""
        converted_data = self._convert_update_data(data)
        updated_data = await self._client.http.put(
            f"/{self._endpoint}/{self.id}", json=converted_data
        )
        if isinstance(updated_data, dict):
            self._update_from_dict(updated_data)
        return self

    async def delete(self: ClientModelProtocol) -> bool:
        """Delete model via API"""
        await self._client.http.delete(f"/{self._endpoint}/{self.id}")
        return True

    def __str__(self: ClientModelProtocol) -> str:
        """Discord.py-style string representation"""
        # Get first non-None string field value
        if hasattr(self, "model_fields"):
            for field_name in self.model_fields:
                if field_name not in ("id", "created_at", "updated_at"):
                    value = getattr(self, field_name, None)
                    if value and isinstance(value, str):
                        return str(value)

        # Fallback to class name + id
        return f"{self.__class__.__name__} {self.id}"

    def __repr__(self: ClientModelProtocol) -> str:
        """Discord.py-style developer representation"""
        class_name = self.__class__.__name__
        attrs = []

        # Always include id first
        attrs.append(f"id={self.id}")

        # Add first 2-3 meaningful fields
        if hasattr(self, "model_fields"):
            count = 0
            for field_name in self.model_fields:
                if field_name not in ("id", "created_at", "updated_at") and count < 2:
                    value = getattr(self, field_name, None)
                    if value is not None:
                        # Skip empty collections and long strings
                        if isinstance(value, (list, dict)) and not value:
                            continue
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."

                        if isinstance(value, str):
                            attrs.append(f"{field_name}={value!r}")
                        else:
                            attrs.append(f"{field_name}={value}")
                        count += 1

        return f"<{class_name} {' '.join(attrs)}>"
