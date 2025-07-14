"""Simple managers for resources without custom methods"""

from typing import TYPE_CHECKING

from awesome_backend_client.base import BaseCRUDManager

if TYPE_CHECKING:
    from awesome_backend_client.client import UAProjectClient


def JudgingManager(client: "UAProjectClient") -> BaseCRUDManager[dict[str, any]]:
    """Simple judging manager with basic CRUD"""
    return BaseCRUDManager(client, "judgings")


def PurchasedItemManager(client: "UAProjectClient") -> BaseCRUDManager[dict[str, any]]:
    """Simple purchased item manager with basic CRUD"""
    return BaseCRUDManager(client, "purchased-items")


def TicketMessageManager(client: "UAProjectClient") -> BaseCRUDManager[dict[str, any]]:
    """Simple ticket message manager with basic CRUD"""
    return BaseCRUDManager(client, "ticket-messages")


def TokenManager(client: "UAProjectClient") -> BaseCRUDManager[dict[str, any]]:
    """Simple token manager with basic CRUD"""
    return BaseCRUDManager(client, "tokens")


def WebhookLogManager(client: "UAProjectClient") -> BaseCRUDManager[dict[str, any]]:
    """Simple webhook log manager with basic CRUD"""
    return BaseCRUDManager(client, "webhook-logs")
