from datetime import datetime, timezone
from app.core.repository import Repositories

from app.core.model.nodes import FolderNode
from app.core.model.nodes import ProjectNode


class FolderService():
    def __init__(self, repos: Repositories, project: ProjectNode):
        self.repos = repos
        self.project = project

    async def create(self, id: str, name: str, qname: str, description: str, path: str):
        created_at = datetime.now(timezone.utc)
        folder = FolderNode(
            id=id,
            name=name,
            qname=qname,
            description=description,
            path=path,
            created_at=created_at,
            updated_at=created_at,
        )
        return await self.repos.folder_repo.create(folder, self.project.db_name)

    async def get(self, folder_id: str):
        return await self.repos.folder_repo.get_by_id(folder_id, self.project.db_name)

    async def update(self, folder: FolderNode):
        return await self.repos.folder_repo.update(folder, self.project.db_name)

    async def delete(self, folder_key: str):
        return await self.repos.folder_repo.delete(folder_key, self.project.db_name)

    async def add_folder(self, parent_folder_id: str, folder_id: str):
        return await self.add_child(parent_folder_id, folder_id)

    async def add_file(self, parent_folder_id: str, file_id: str):
        return await self.add_child(parent_folder_id, file_id)

    async def get_children(self, folder_id: str):
        return await self.repos.folder_repo.get_containment_tree(folder_id)
