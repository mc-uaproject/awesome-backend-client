"""Managers package for UAProject backend client"""

from awesome_backend_client.base import BaseCRUDManager

from .application import ApplicationManager
from .application_section import ApplicationSectionManager
from .balance import BalanceManager
from .debug import DebugManager
from .file import FileManager
from .punishment import PunishmentManager
from .role import RoleManager
from .service import ServiceManager
from .transaction import TransactionManager
from .user import UserManager
from .webhook import WebhookManager
from .webhook_log import WebhookLogManager

__all__ = [
    "ApplicationManager",
    "ApplicationSectionManager",
    "BalanceManager",
    "BaseCRUDManager",
    "ClaimManager",
    "DebugManager",
    "FileManager",
    "JudgingManager",
    "NewsManager",
    "PunishmentManager",
    "PunishmentConfigManager",
    "PurchasedItemManager",
    "RoleManager",
    "ServiceManager",
    "TicketManager",
    "TicketMessageManager",
    "TokenManager",
    "TransactionManager",
    "UserManager",
    "WebhookManager",
    "WebhookLogManager",
]
