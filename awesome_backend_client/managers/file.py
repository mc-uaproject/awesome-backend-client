"""Simple file manager with basic CRUD"""

from typing import TYPE_CHECKING

from uaproject_backend_schemas.models.file import (
    File as FileSchema,
)

from awesome_backend_client.base import BaseCRUDManager
from awesome_backend_client.models.file import File

if TYPE_CHECKING:
    from uaproject_backend_schemas.models.file import (
        FileFilter,
        FileSchemaCreate,
        FileSchemaUpdate,
    )

    from awesome_backend_client.client import UAProjectClient
else:
    FileFilter = FileSchema.filter
    FileSchemaCreate = FileSchema.schemas.create
    FileSchemaUpdate = FileSchema.schemas.update


class FileManager(
    BaseCRUDManager[File, FileSchemaCreate, FileSchemaUpdate, FileFilter]
):
    """Simple file manager with basic CRUD"""

    def __init__(self, client: "UAProjectClient"):
        from awesome_backend_client.models import File

        super().__init__(client, "files", File)
