"""
Enhanced payload classes for event handling.

Provides dict-like objects with dot notation access for convenient event data handling.
"""

from typing import Any, Union


class DotDict(dict):
    """
    Dictionary that allows access to items using dot notation.

    Features:
    - Access items with dot notation: payload.data.user.name
    - Works like regular dict: payload['data']['user']['name']
    - Supports nested access and creation
    - JSON serializable
    - Type hints friendly

    Example:
        payload = DotDict({
            'event': 'create',
            'data': {
                'user': {
                    'id': 123,
                    'name': 'TestUser'
                }
            }
        })

        # Dot notation access
        print(payload.event)              # 'create'
        print(payload.data.user.name)     # 'TestUser'

        # Dict-style access (still works)
        print(payload['data']['user']['id'])  # 123

        # Assignment with dot notation
        payload.data.user.status = 'active'
        payload.new_field = 'value'
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert nested dictionaries to DotDict
        for key, value in self.items():
            if isinstance(value, dict) and not isinstance(value, DotDict):
                self[key] = DotDict(value)
            elif isinstance(value, list):
                self[key] = self._convert_list(value)

    def _convert_list(self, lst):
        """Convert list items that are dicts to DotDict"""
        return [
            DotDict(item)
            if isinstance(item, dict) and not isinstance(item, DotDict)
            else self._convert_list(item)
            if isinstance(item, list)
            else item
            for item in lst
        ]

    def __getattr__(self, key: str) -> Any:
        """Allow dot notation access for getting values"""
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            ) from e

    def __setattr__(self, key: str, value: Any) -> None:
        """Allow dot notation access for setting values"""
        if key.startswith("_") or key in (
            "keys",
            "values",
            "items",
            "get",
            "pop",
            "update",
            "clear",
        ):
            # Avoid conflicts with dict methods and private attributes
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __delattr__(self, key: str) -> None:
        """Allow dot notation access for deleting values"""
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            ) from e

    def __setitem__(self, key: str, value: Any) -> None:
        """Override setitem to convert nested dicts to DotDict"""
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
        elif isinstance(value, list):
            value = self._convert_list(value)
        super().__setitem__(key, value)

    def __getstate__(self) -> dict[str, Any]:
        """Support for pickling"""
        return dict(self)

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Support for unpickling"""
        self.clear()
        self.update(state)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default, maintains dot notation for returned dicts"""
        value = super().get(key, default)
        if isinstance(value, dict) and not isinstance(value, DotDict):
            return DotDict(value)
        return value

    def update(self, *args, **kwargs) -> None:
        """Update dictionary, converting nested dicts to DotDict"""
        if args:
            other = args[0]
            if hasattr(other, "items"):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert back to regular dictionary recursively"""
        result = {}
        for key, value in self.items():
            if isinstance(value, DotDict):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = self._convert_list_to_dict(value)
            else:
                result[key] = value
        return result

    def _convert_list_to_dict(self, lst):
        """Convert list with DotDict items back to regular dicts"""
        return [
            item.to_dict()
            if isinstance(item, DotDict)
            else self._convert_list_to_dict(item)
            if isinstance(item, list)
            else item
            for item in lst
        ]

    def __repr__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}({dict.__repr__(self)})"

    def __str__(self) -> str:
        """String representation"""
        return dict.__str__(self)


class EventPayload(DotDict):
    """
    Enhanced payload for event handling with additional convenience methods.

    Provides structured access to common event fields and metadata.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure required fields exist with defaults
        self.setdefault("source", "unknown")
        self.setdefault("timestamp", self._get_current_timestamp())
        self.setdefault("data", DotDict())
        self.setdefault("metadata", DotDict())

    @property
    def event_type(self) -> str:
        """Get event type (e.g., 'create', 'update', 'delete')"""
        return self.get("event", self.get("action", "unknown"))

    @property
    def model_name(self) -> str:
        """Get model name (e.g., 'User', 'Application')"""
        return self.get("model", "unknown")

    @property
    def event_pattern(self) -> str:
        """Get full event pattern (e.g., 'User.create')"""
        return f"{self.model_name}.{self.event_type}"

    @property
    def user_id(self) -> Union[int, None]:
        """Get user ID from various possible locations"""
        # Try different common locations for user_id
        if "user_id" in self:
            return self.user_id
        elif hasattr(self.data, "user_id"):
            return self.data.user_id
        elif hasattr(self.data, "id") and self.model_name.lower() == "user":
            return self.data.id
        elif hasattr(self.data, "user") and hasattr(self.data.user, "id"):
            return self.data.user.id
        return None

    @property
    def entity_id(self) -> Union[int, str, None]:
        """Get entity ID (the main object's ID)"""
        if hasattr(self.data, "id"):
            return self.data.id
        return self.get("id")

    @property
    def is_websocket(self) -> bool:
        """Check if this is a WebSocket event"""
        return self.source == "websocket"

    @property
    def is_webhook(self) -> bool:
        """Check if this is a Webhook event"""
        return self.source == "webhook"

    @property
    def has_changes(self) -> bool:
        """Check if this event has old_data (indicating changes)"""
        return "old_data" in self and self.old_data

    @property
    def changed_fields(self) -> list[str]:
        """Get list of fields that changed (if old_data is available)"""
        if not self.has_changes:
            return []

        changed = []
        old_data = self.get("old_data", {})
        current_data = self.get("data", {})

        # Compare top-level fields
        all_fields = set(old_data.keys()) | set(current_data.keys())
        for field in all_fields:
            old_value = old_data.get(field)
            new_value = current_data.get(field)
            if old_value != new_value:
                changed.append(field)

        return changed

    def get_field_change(self, field: str) -> dict[str, Any]:
        """Get before/after values for a specific field"""
        if not self.has_changes:
            return {"old": None, "new": None, "changed": False}

        old_data = self.get("old_data", {})
        current_data = self.get("data", {})

        old_value = old_data.get(field)
        new_value = current_data.get(field)

        return {"old": old_value, "new": new_value, "changed": old_value != new_value}

    def was_field_changed(self, field: str) -> bool:
        """Check if a specific field was changed"""
        return self.get_field_change(field)["changed"]

    def add_metadata(self, **kwargs) -> None:
        """Add metadata to the event payload"""
        if not hasattr(self, "metadata"):
            self.metadata = DotDict()
        self.metadata.update(kwargs)

    def get_nested(self, path: str, default: Any = None) -> Any:
        """
        Get nested value using dot notation path.

        Example:
            payload.get_nested('data.user.profile.name', 'Unknown')
        """
        parts = path.split(".")
        current = self

        try:
            for part in parts:
                if isinstance(current, (dict, DotDict)):
                    current = current[part]
                else:
                    return default
            return current
        except (KeyError, AttributeError, TypeError):
            return default

    def set_nested(self, path: str, value: Any) -> None:
        """
        Set nested value using dot notation path.

        Example:
            payload.set_nested('data.user.profile.name', 'NewName')
        """
        parts = path.split(".")
        current = self

        # Navigate to the parent of the target
        for part in parts[:-1]:
            if part not in current:
                current[part] = DotDict()
            current = current[part]

        # Set the final value
        current[parts[-1]] = value

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def __repr__(self) -> str:
        """Enhanced string representation for debugging"""
        return (
            f"EventPayload({self.event_pattern}, "
            f"source={self.source}, id={self.entity_id})"
        )


class WebSocketPayload(EventPayload):
    """Specialized payload for WebSocket events"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = "websocket"
        self.setdefault("real_time", True)


class WebhookPayload(EventPayload):
    """Specialized payload for Webhook events"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = "webhook"
        self.setdefault("delivery_id", None)
        self.setdefault("attempt", 1)


def create_payload(data: dict[str, Any], source: str = "unknown") -> EventPayload:
    """
    Factory function to create appropriate payload type.

    Args:
        data: Raw payload data
        source: Event source ('websocket', 'webhook', etc.)

    Returns:
        Appropriate payload instance
    """
    if source == "websocket":
        return WebSocketPayload(data)
    elif source == "webhook":
        return WebhookPayload(data)
    else:
        return EventPayload(data)


# Export main classes
__all__ = [
    "DotDict",
    "EventPayload",
    "WebSocketPayload",
    "WebhookPayload",
    "create_payload",
]
