"""Models package for UAProject backend client"""

# Import BaseBackendModel from base for backwards compatibility
from awesome_backend_client.base import BaseBackendModel as BaseModel

from .application import Application
from .balance import Balance
from .file import File
from .punishment import Punishment
from .role import Role
from .service import Service
from .transaction import Transaction
from .user import User
from .webhook import Webhook
from .webhook_log import WebhookLog

__all__ = [
    "Application",
    "Balance",
    "BaseModel",
    "File",
    "Punishment",
    "Role",
    "Service",
    "Transaction",
    "User",
    "Webhook",
    "WebhookLog",
]
