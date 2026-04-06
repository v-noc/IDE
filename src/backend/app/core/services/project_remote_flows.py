"""Orchestration for create_remote and clone project setup (see doc/remote-project-setup/)."""

from datetime import datetime, timezone

from slugify import slugify

from app.api.schemas.terminus_remote import (
    RemoteConfig,
    clone_source_for_remote_database,
    remote_auth_to_header_dict,
)
from app.config.settings import get_settings
from app.core.model import ProjectNode
from app.core.model.schemas import ProjectSchema
from app.core.repository.project_bootstrap import bootstrap_empty_project_database
from app.core.repository.project_repo import ProjectRepo
from app.db.async_terminus_client import AsyncClient
from app.db.remote_terminus import remote_terminus_client


async def _pick_unused_local_db_name(local_client: AsyncClient, name: str) -> str:
    """Choose local db id from project name without creating a database (clone path)."""
    base = slugify(name)
    admin = local_client.clone()
    if not await admin.has_database(base):
        return base
    return f"{base}_{datetime.now().strftime('%Y%m%d%H%M%S')}"


async def create_with_remote_bootstrap(
    *,
    project_repo: ProjectRepo,
    local_client: AsyncClient,
    name: str,
    description: str,
    path: str,
    remote: RemoteConfig,
) -> ProjectNode:
    settings = get_settings()
    team = remote.team or settings.TERMINUS_TEAM
    auth = remote.auth
    remote_auth = remote_auth_to_header_dict(auth)

    connect_user = auth.username or settings.TERMINUS_USER

    async with remote_terminus_client(
        remote.remote_url,
        user=connect_user,
        key=auth.key,
        team=team,
    ) as remote_client:
        db_name = await bootstrap_empty_project_database(
            remote_client.clone(),
            name,
            description,
        )

    project_node = await project_repo.register_project(
        name=name,
        description=description,
        path=path,
        db_name=db_name,
    )

    clone_source = clone_source_for_remote_database(remote.remote_url, team, db_name)
    local_admin = local_client.clone()
    await local_admin.clonedb(
        clone_source=clone_source,
        newid=db_name,
        description=description or f"Clone {name}",
        remote_auth=remote_auth,
    )
    return project_node


async def create_from_remote_clone(
    *,
    project_repo: ProjectRepo,
    local_client: AsyncClient,
    name: str,
    description: str,
    path: str,
    remote: RemoteConfig,
) -> ProjectNode:
    newid = await _pick_unused_local_db_name(local_client, name)
    remote_auth = remote_auth_to_header_dict(remote.auth)

    local_admin = local_client.clone()
    await local_admin.clonedb(
        clone_source=remote.remote_url,
        newid=newid,
        description=description or f"Clone {name}",
        remote_auth=remote_auth,
    )

    return await project_repo.register_project(
        name=name,
        description=description,
        path=path,
        db_name=newid,
    )
