"""File model with methods for file operations"""

import logging
from typing import TYPE_CHECKING

import httpx
from uaproject_backend_schemas.models import (
    File as FileSchema,
)

from awesome_backend_client.base import BaseBackendModel

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.file import FileSchemaResponse

    from awesome_backend_client.client import UAProjectClient
else:
    FileSchemaResponse = FileSchema.schemas.response

logger = logging.getLogger(__name__)


class File(BaseBackendModel, FileSchemaResponse):
    """
    File model with methods for file operations
    """

    def __init__(self, file_schema: FileSchemaResponse, *, client: "UAProjectClient"):
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
