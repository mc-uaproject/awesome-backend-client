"""
Model wrappers for UAProject API objects

These models provide a discord.py-like interface over the schema objects,
with methods for performing actions and accessing related objects.
Uses existing schemas from uaproject-backend-schemas - no duplication.
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

import httpx
from uaproject_backend_schemas.models import (
    Application as ApplicationSchema,
)
from uaproject_backend_schemas.models import (
    Balance as BalanceSchema,
)
from uaproject_backend_schemas.models import (
    File as FileSchema,
)
from uaproject_backend_schemas.models import (
    Punishment as PunishmentSchema,
)
from uaproject_backend_schemas.models import (
    Role as RoleSchema,
)
from uaproject_backend_schemas.models import (
    Service as ServiceSchema,
)
from uaproject_backend_schemas.models import (
    Transaction as TransactionSchema,
)
from uaproject_backend_schemas.models import (
    User as UserSchema,
)
from uaproject_backend_schemas.models import (
    Webhook as WebhookSchema,
)

if TYPE_CHECKING:
    from .client import UAProjectClient

logger = logging.getLogger(__name__)


class BaseModel:
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


class User(BaseModel):
    """
    User model with methods for user operations

    Wraps UserSchema from uaproject-backend-schemas and adds convenience methods.
    All UserSchema properties are accessible directly
    (id, discord_id, minecraft_nickname, etc.)
    """

    def __init__(self, user_schema: UserSchema, *, client: "UAProjectClient"):
        super().__init__(user_schema, client=client)

    async def refresh(self):
        """Refresh user data from API"""
        try:
            fresh_data = await self._client.users.get(self.id)
            # Convert dict response to UserSchema
            self._schema = UserSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh user {self.id}: {e}")

    async def edit(self, **fields) -> "User":
        """Edit user fields (discord.py style)"""
        updated_data = await self._client.users.update(self.id, fields)
        self._schema = UserSchema.model_validate(updated_data)
        return self

    async def delete(self) -> bool:
        """Delete user"""
        return await self._client.users.delete(self.id)

    async def get_balance(self) -> Optional["Balance"]:
        """Get user's balance"""
        try:
            balance_data = await self._client.balances.get_many(
                filters={"user_id": self.id}
            )
            if balance_data:
                balance_schema = BalanceSchema.model_validate(balance_data[0])
                return Balance(balance_schema, client=self._client)
        except Exception:
            pass
        return None

    async def get_applications(self) -> list["Application"]:
        """Get user's applications"""
        try:
            apps_data = await self._client.applications.get_many(
                filters={"user_id": self.id}
            )
            return [
                Application(ApplicationSchema.model_validate(app), client=self._client)
                for app in apps_data
            ]
        except Exception:
            return []

    async def get_punishments(self, active_only: bool = True) -> list["Punishment"]:
        """Get user's punishments"""
        try:
            filters = {"user_id": self.id}
            if active_only:
                filters["is_active"] = True

            punishments_data = await self._client.punishments.get_many(filters=filters)
            return [
                Punishment(PunishmentSchema.model_validate(p), client=self._client)
                for p in punishments_data
            ]
        except Exception:
            return []

    async def add_balance(
        self, amount: float, reason: str = "Manual adjustment"
    ) -> "Transaction":
        """Add balance to user"""
        transaction_data = await self._client.transactions.create(
            {"user_id": self.id, "amount": amount, "type": "credit", "reason": reason}
        )
        transaction_schema = TransactionSchema.model_validate(transaction_data)
        return Transaction(transaction_schema, client=self._client)

    async def remove_balance(
        self, amount: float, reason: str = "Manual adjustment"
    ) -> "Transaction":
        """Remove balance from user"""
        transaction_data = await self._client.transactions.create(
            {
                "user_id": self.id,
                "amount": -abs(amount),
                "type": "debit",
                "reason": reason,
            }
        )
        transaction_schema = TransactionSchema.model_validate(transaction_data)
        return Transaction(transaction_schema, client=self._client)

    def __str__(self) -> str:
        # Use minecraft_nickname if available, fallback to id
        nickname = getattr(self._schema, "minecraft_nickname", None)
        return f"User(id={self.id}, nickname='{nickname or 'Unknown'}')"

    def __repr__(self) -> str:
        nickname = getattr(self._schema, "minecraft_nickname", None)
        return f"<User id={self.id} nickname='{nickname or 'Unknown'}'>"


class Application(BaseModel):
    """
    Application model with methods for application operations

    Wraps ApplicationSchema from uaproject-backend-schemas and adds convenience methods.
    """

    def __init__(self, app_schema: ApplicationSchema, *, client: "UAProjectClient"):
        super().__init__(app_schema, client=client)

    async def refresh(self):
        """Refresh application data from API"""
        try:
            fresh_data = await self._client.applications.get(self.id)
            self._schema = ApplicationSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh application {self.id}: {e}")

    async def approve(self, reason: str = "") -> "Application":
        """Approve this application"""
        updated_data = await self._client.applications.update(
            self.id, {"status": "approved", "admin_notes": reason}
        )
        self._schema = ApplicationSchema.model_validate(updated_data)
        return self

    async def reject(self, reason: str = "") -> "Application":
        """Reject this application"""
        updated_data = await self._client.applications.update(
            self.id, {"status": "rejected", "admin_notes": reason}
        )
        self._schema = ApplicationSchema.model_validate(updated_data)
        return self

    async def edit(self, **fields) -> "Application":
        """Edit application fields"""
        updated_data = await self._client.applications.update(self.id, fields)
        self._schema = ApplicationSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional[User]:
        """Get the user who submitted this application"""
        try:
            user_data = await self._client.users.get(self.user_id)
            return User(UserSchema.model_validate(user_data), client=self._client)
        except Exception:
            return None

    async def get_service(self) -> Optional["Service"]:
        """Get the service this application is for"""
        try:
            service_data = await self._client.services.get(self.service_id)
            return Service(
                ServiceSchema.model_validate(service_data), client=self._client
            )
        except Exception:
            return None

    def __str__(self) -> str:
        return (
            f"Application(id={self.id}, status='{self.status}', user_id={self.user_id})"
        )

    def __repr__(self) -> str:
        return (
            f"<Application id={self.id} status='{self.status}' user_id={self.user_id}>"
        )


class Service(BaseModel):
    """
    Service model with methods for service operations
    """

    def __init__(self, service_schema: ServiceSchema, *, client: "UAProjectClient"):
        super().__init__(service_schema, client=client)

    async def refresh(self):
        """Refresh service data from API"""
        try:
            fresh_data = await self._client.services.get(self.id)
            self._schema = ServiceSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh service {self.id}: {e}")

    async def edit(self, **fields) -> "Service":
        """Edit service fields"""
        updated_data = await self._client.services.update(self.id, fields)
        self._schema = ServiceSchema.model_validate(updated_data)
        return self

    async def get_applications(
        self, *, status: Optional[str] = None, limit: int = 50
    ) -> list[Application]:
        """Get applications for this service"""
        try:
            filters = {"service_id": self.id}
            if status:
                filters["status"] = status

            apps_data = await self._client.applications.get_many(
                filters=filters, limit=limit
            )
            return [
                Application(ApplicationSchema.model_validate(app), client=self._client)
                for app in apps_data
            ]
        except Exception:
            return []

    def __str__(self) -> str:
        return f"Service(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        return f"<Service id={self.id} name='{self.name}'>"


class Balance(BaseModel):
    """
    Balance model with methods for balance operations
    """

    def __init__(self, balance_schema: BalanceSchema, *, client: "UAProjectClient"):
        super().__init__(balance_schema, client=client)

    async def refresh(self):
        """Refresh balance data from API"""
        try:
            fresh_data = await self._client.balances.get(self.id)
            self._schema = BalanceSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh balance {self.id}: {e}")

    async def edit(self, **fields) -> "Balance":
        """Edit balance fields"""
        updated_data = await self._client.balances.update(self.id, fields)
        self._schema = BalanceSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional[User]:
        """Get the user who owns this balance"""
        try:
            user_data = await self._client.users.get(self.user_id)
            return User(UserSchema.model_validate(user_data), client=self._client)
        except Exception:
            return None

    def __str__(self) -> str:
        return f"Balance(id={self.id}, amount={self.amount}, user_id={self.user_id})"

    def __repr__(self) -> str:
        return f"<Balance id={self.id} amount={self.amount} user_id={self.user_id}>"


class Transaction(BaseModel):
    """
    Transaction model with methods for transaction operations
    """

    def __init__(
        self, transaction_schema: TransactionSchema, *, client: "UAProjectClient"
    ):
        super().__init__(transaction_schema, client=client)

    async def refresh(self):
        """Refresh transaction data from API"""
        try:
            fresh_data = await self._client.transactions.get(self.id)
            self._schema = TransactionSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh transaction {self.id}: {e}")

    async def edit(self, **fields) -> "Transaction":
        """Edit transaction fields"""
        updated_data = await self._client.transactions.update(self.id, fields)
        self._schema = TransactionSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional[User]:
        """Get the user who made this transaction"""
        try:
            user_data = await self._client.users.get(self.user_id)
            return User(UserSchema.model_validate(user_data), client=self._client)
        except Exception:
            return None

    def __str__(self) -> str:
        return f"Transaction(id={self.id}, amount={self.amount}, type='{self.type}')"

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} amount={self.amount} type='{self.type}'>"


class Punishment(BaseModel):
    """
    Punishment model with methods for punishment operations
    """

    def __init__(
        self, punishment_schema: PunishmentSchema, *, client: "UAProjectClient"
    ):
        super().__init__(punishment_schema, client=client)

    async def refresh(self):
        """Refresh punishment data from API"""
        try:
            fresh_data = await self._client.punishments.get(self.id)
            self._schema = PunishmentSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh punishment {self.id}: {e}")

    async def edit(self, **fields) -> "Punishment":
        """Edit punishment fields"""
        updated_data = await self._client.punishments.update(self.id, fields)
        self._schema = PunishmentSchema.model_validate(updated_data)
        return self

    async def revoke(self, reason: str = "Manually revoked") -> "Punishment":
        """Revoke this punishment"""
        updated_data = await self._client.punishments.update(
            self.id, {"is_active": False, "revoke_reason": reason}
        )
        self._schema = PunishmentSchema.model_validate(updated_data)
        return self

    async def get_user(self) -> Optional[User]:
        """Get the user who received this punishment"""
        try:
            user_data = await self._client.users.get(self.user_id)
            return User(UserSchema.model_validate(user_data), client=self._client)
        except Exception:
            return None

    def __str__(self) -> str:
        return f"Punishment(id={self.id}, type='{self.type}', active={self.is_active})"

    def __repr__(self) -> str:
        return f"<Punishment id={self.id} type='{self.type}' active={self.is_active}>"


class Role(BaseModel):
    """
    Role model with methods for role operations
    """

    def __init__(self, role_schema: RoleSchema, *, client: "UAProjectClient"):
        super().__init__(role_schema, client=client)

    async def refresh(self):
        """Refresh role data from API"""
        try:
            fresh_data = await self._client.roles.get(self.id)
            self._schema = RoleSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh role {self.id}: {e}")

    async def edit(self, **fields) -> "Role":
        """Edit role fields"""
        updated_data = await self._client.roles.update(self.id, fields)
        self._schema = RoleSchema.model_validate(updated_data)
        return self

    async def add_permission(self, permission: str) -> "Role":
        """Add permission to role"""
        current_permissions = getattr(self._schema, "permissions", []) or []
        if permission not in current_permissions:
            current_permissions.append(permission)
            await self.edit(permissions=current_permissions)
        return self

    async def remove_permission(self, permission: str) -> "Role":
        """Remove permission from role"""
        current_permissions = getattr(self._schema, "permissions", []) or []
        if permission in current_permissions:
            current_permissions.remove(permission)
            await self.edit(permissions=current_permissions)
        return self

    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        permissions = getattr(self._schema, "permissions", []) or []
        return permission in permissions

    def __str__(self) -> str:
        return f"Role(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        return f"<Role id={self.id} name='{self.name}'>"


class File(BaseModel):
    """
    File model with methods for file operations
    """

    def __init__(self, file_schema: FileSchema, *, client: "UAProjectClient"):
        super().__init__(file_schema, client=client)

    async def refresh(self):
        """Refresh file data from API"""
        try:
            fresh_data = await self._client.files.get(self.id)
            self._schema = FileSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh file {self.id}: {e}")

    async def edit(self, **fields) -> "File":
        """Edit file fields"""
        updated_data = await self._client.files.update(self.id, fields)
        self._schema = FileSchema.model_validate(updated_data)
        return self

    async def download(self) -> bytes:
        """Download file content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)
            return response.content

    async def delete(self) -> bool:
        """Delete this file"""
        return await self._client.files.delete(self.id)

    def __str__(self) -> str:
        return f"File(id={self.id}, filename='{self.filename}')"

    def __repr__(self) -> str:
        return f"<File id={self.id} filename='{self.filename}'>"


class Webhook(BaseModel):
    """
    Webhook model with methods for webhook operations
    """

    def __init__(self, webhook_schema: WebhookSchema, *, client: "UAProjectClient"):
        super().__init__(webhook_schema, client=client)

    async def refresh(self):
        """Refresh webhook data from API"""
        try:
            fresh_data = await self._client.webhooks.get(self.id)
            self._schema = WebhookSchema.model_validate(fresh_data)
        except Exception as e:
            logger.error(f"Failed to refresh webhook {self.id}: {e}")

    async def edit(self, **fields) -> "Webhook":
        """Edit webhook fields"""
        updated_data = await self._client.webhooks.update(self.id, fields)
        self._schema = WebhookSchema.model_validate(updated_data)
        return self

    async def update_events(self, events: list[str]) -> "Webhook":
        """Update webhook events"""
        return await self.edit(events=events)

    async def activate(self) -> "Webhook":
        """Activate webhook"""
        return await self.edit(is_active=True)

    async def deactivate(self) -> "Webhook":
        """Deactivate webhook"""
        return await self.edit(is_active=False)

    async def delete(self) -> bool:
        """Delete this webhook"""
        return await self._client.webhooks.delete(self.id)

    def __str__(self) -> str:
        return f"Webhook(id={self.id}, url='{self.url}')"

    def __repr__(self) -> str:
        return f"<Webhook id={self.id} url='{self.url}'>"
