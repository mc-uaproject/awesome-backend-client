"""Models package for UAProject backend client"""

# Import BaseBackendModel from base for backwards compatibility
from awesome_backend_client.base import BaseBackendModel as BaseModel

from .user import User

__all__ = [
    "BaseModel",
    "User",
]
