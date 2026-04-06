"""Empty project graph bootstrap (create DB + schema + root folder) on any Terminus client."""

from datetime import datetime

from slugify import slugify

from app.db.async_terminus_client import AsyncClient
from app.db.errors import DatabaseError
from app.core.model.schemas import FolderSchema, ensure_schema


def _database_already_exists(err: DatabaseError) -> bool:
    api_err = err.error_obj.get("api:error") or err.error_obj.get("api.error") or {}
    return api_err.get("@type", "") == "api:DatabaseAlreadyExists"


async def bootstrap_empty_project_database(
    data_plane: AsyncClient,
    name: str,
    description: str,
) -> str:
    """
    Create a new database on the server `data_plane` is connected to, apply V-NOC schema,
    and insert the init folder. Returns the database id used.
    """
    db_name = slugify(name)
    clone_db = data_plane.clone()

    try:
        await clone_db.create_database(
            db_name,
            label=db_name,
            description="V-NOC code analysis graph",
        )
    except DatabaseError as e:
        if _database_already_exists(e):
            db_name = f"{db_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            await clone_db.create_database(
                db_name,
                label=db_name,
                description="V-NOC code analysis graph",
            )
        else:
            raise

    await ensure_schema(
        clone_db,
        f"{name} Schema",
        description,
        [f"{name} Team"],
    )
    init_folder = FolderSchema.create_init_folder()
    await clone_db.insert_document(
        init_folder,
        commit_msg="Add __init__ global document theme folder",
    )
    return db_name
