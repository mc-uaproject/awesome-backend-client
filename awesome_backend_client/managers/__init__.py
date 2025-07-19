"""Managers package for UAProject backend client"""

from awesome_backend_client.base import BaseCRUDManager

from .user import UserManager

__all__ = [
    "BaseCRUDManager",
    "UserManager",
]
