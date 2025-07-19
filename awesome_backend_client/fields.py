"""
WebhookField - custom field for pydantic models with additional settings
"""

from typing import Any

from pydantic import Field


def WebhookField(
    default: Any = ...,
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    examples: list | None = None,
    exclude: bool | None = None,
    include: bool | None = None,
    discriminator: str | None = None,
    json_schema_extra: dict[str, Any] | None = None,
    frozen: bool | None = None,
    validate_default: bool | None = None,
    repr: bool = True,
    init_var: bool | None = None,
    kw_only: bool | None = None,
    pattern: str | None = None,
    strict: bool | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    allow_inf_nan: bool | None = None,
    max_length: int | None = None,
    min_length: int | None = None,
    # Custom webhook settings
    webhook_field: bool = False,
    sensitive: bool = False,
    audit_log: bool = False,
    cache_key: str | None = None,
    validation_level: str = "strict",
    **kwargs: Any,
) -> Any:
    """
    Creates a custom field for webhooks with additional settings.

    Args:
        webhook_field: Whether the field is part of webhook payload
        sensitive: Whether the field contains sensitive data (for logging)
        audit_log: Whether to log changes to this field in audit log
        cache_key: Key for caching field value
        validation_level: Validation level ('strict', 'relaxed', 'disabled')
        **kwargs: Other parameters passed to Field()
    """

    # Create additional metadata for the field
    webhook_metadata = {
        "webhook_field": webhook_field,
        "sensitive": sensitive,
        "audit_log": audit_log,
        "cache_key": cache_key,
        "validation_level": validation_level,
    }

    # Merge with existing json_schema_extra
    if json_schema_extra is None:
        json_schema_extra = {}

    json_schema_extra.update({"webhook_metadata": webhook_metadata})

    return Field(  # type: ignore[call-overload,misc]
        default,
        alias=alias,
        title=title,
        description=description,
        examples=examples,
        exclude=exclude,
        discriminator=discriminator,
        json_schema_extra=json_schema_extra,
        frozen=frozen,
        validate_default=validate_default,
        repr=repr,
        init_var=init_var,
        kw_only=kw_only,
        pattern=pattern,
        strict=strict,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_length=max_length,
        min_length=min_length,
        **kwargs,
    )


def get_webhook_metadata(field_info: Any) -> dict[str, Any]:
    """
    Extracts webhook metadata from field info.

    Args:
        field_info: Pydantic field information

    Returns:
        Dictionary with webhook metadata
    """
    if hasattr(field_info, "json_schema_extra") and field_info.json_schema_extra:
        metadata = field_info.json_schema_extra.get("webhook_metadata", {})
        return metadata if isinstance(metadata, dict) else {}
    return {}


def is_webhook_field(field_info: Any) -> bool:
    """Checks if the field is a webhook field."""
    metadata = get_webhook_metadata(field_info)
    result = metadata.get("webhook_field", False)
    return bool(result)


def is_sensitive_field(field_info: Any) -> bool:
    """Checks if the field is sensitive."""
    metadata = get_webhook_metadata(field_info)
    result = metadata.get("sensitive", False)
    return bool(result)


def should_audit_field(field_info: Any) -> bool:
    """Checks if field changes should be logged in audit log."""
    metadata = get_webhook_metadata(field_info)
    result = metadata.get("audit_log", False)
    return bool(result)


def get_cache_key(field_info: Any) -> str | None:
    """Gets the cache key for the field."""
    return get_webhook_metadata(field_info).get("cache_key")


def get_validation_level(field_info: Any) -> str:
    """Gets the validation level for the field."""
    metadata = get_webhook_metadata(field_info)
    result = metadata.get("validation_level", "strict")
    return str(result)
