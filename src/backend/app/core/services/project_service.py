import asyncio
from typing import Optional

from app.api.schemas.terminus_remote import RemoteConfig
from app.core.model.nodes import FolderNode, ProjectNode
from app.core.model.schemas import FileSchema, FolderSchema, StructureGroupSchema
from app.db.async_terminus_client import AsyncClient
from app.db.context import ProjectUoW


class ProjectService():
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.project_repos = self.uow.get_project_repos()
        self.meta_repos = self.uow.get_meta_repos()

    async def delete(self, project_id: str):
        return await self.meta_repos.project_repo.delete(project_id)

    async def update(self, project: ProjectNode):
        return await self.meta_repos.project_repo.update(project.id, project)

    async def create_node(self, project: ProjectNode):
        return await self.meta_repos.project_repo.create(project)

    async def create(self, name: str, description: str, path: str):
        return await self.meta_repos.project_repo.create(name, description, path)

    async def create_with_remote_bootstrap(
        self,
        local_client: AsyncClient,
        name: str,
        description: str,
        path: str,
        remote: RemoteConfig,
    ) -> ProjectNode:
        from app.core.services.project_remote_flows import (
            create_with_remote_bootstrap as remote_bootstrap,
        )

        return await remote_bootstrap(
            project_repo=self.meta_repos.project_repo,
            local_client=local_client,
            name=name,
            description=description,
            path=path,
            remote=remote,
        )

    async def create_from_remote_clone(
        self,
        local_client: AsyncClient,
        name: str,
        description: str,
        path: str,
        remote: RemoteConfig,
    ) -> ProjectNode:
        from app.core.services.project_remote_flows import (
            create_from_remote_clone as remote_clone,
        )

        return await remote_clone(
            project_repo=self.meta_repos.project_repo,
            local_client=local_client,
            name=name,
            description=description,
            path=path,
            remote=remote,
        )

    async def get(self, project_id: str):
        return await self.meta_repos.project_repo.get_by_id(project_id)

    async def get_all(self):
        return await self.meta_repos.project_repo.get_all()

    async def get_structure(
        self,
        exclude_types: list[str] = [],
        include_commit_id: bool = False,
        compare_to: Optional[bool] = False,
    ):
        project_repos = self.uow.get_project_repos()
        if compare_to:
            project_repos = self.uow.get_project_repos(use_compare_to=True)
        repo = project_repos.structure_repo
        client = repo.client
        to_node = repo._to_node
        load_groups = StructureGroupSchema.__name__ not in set(exclude_types)

        if include_commit_id:
            if load_groups:
                (folders_raw, version), files_raw, groups_raw = await asyncio.gather(
                    client.get_all_documents(
                        doc_type=FolderSchema.__name__,
                        get_data_version=True,
                        as_list=True,
                    ),
                    client.get_all_documents(
                        doc_type=FileSchema.__name__,
                        as_list=True,
                    ),
                    client.get_all_documents(
                        doc_type=StructureGroupSchema.__name__,
                        as_list=True,
                    ),
                )
            else:
                (folders_raw, version), files_raw = await asyncio.gather(
                    client.get_all_documents(
                        doc_type=FolderSchema.__name__,
                        get_data_version=True,
                        as_list=True,
                    ),
                    client.get_all_documents(
                        doc_type=FileSchema.__name__,
                        as_list=True,
                    ),
                )
                groups_raw = []
        else:
            if load_groups:
                folders_raw, files_raw, groups_raw = await asyncio.gather(
                    client.get_all_documents(
                        doc_type=FolderSchema.__name__,
                        as_list=True,
                    ),
                    client.get_all_documents(
                        doc_type=FileSchema.__name__,
                        as_list=True,
                    ),
                    client.get_all_documents(
                        doc_type=StructureGroupSchema.__name__,
                        as_list=True,
                    ),
                )
            else:
                folders_raw, files_raw = await asyncio.gather(
                    client.get_all_documents(
                        doc_type=FolderSchema.__name__,
                        as_list=True,
                    ),
                    client.get_all_documents(
                        doc_type=FileSchema.__name__,
                        as_list=True,
                    ),
                )
                groups_raw = []
            version = None

        merged = []
        for raw in folders_raw + files_raw + groups_raw:
            node = to_node(raw)
            if isinstance(node, FolderNode) and node.is_root:
                continue
            merged.append(node)

        return merged, version

    async def get_children(self, exclude_types: list[str] = [],  include_commit_id: bool = False, compare_to: Optional[bool] = False):
        project_repos = self.uow.get_project_repos()
        if compare_to:
            project_repos = self.uow.get_project_repos(
                use_compare_to=True)
            return await project_repos.project_repo.get_children(
                exclude_types,
                include_commit_id,
            )
        return await project_repos.project_repo.get_children(
            exclude_types,
            include_commit_id,
        )
