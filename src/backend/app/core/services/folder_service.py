from datetime import datetime, timezone
from typing import List, Literal, Tuple

from app.core.model.nodes import FolderNode
from app.db.context import ProjectUoW


class FolderService():
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()

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
        return await self.repos.folder_repo.create(folder)

    async def get(self, folder_id: str):
        return await self.repos.folder_repo.get_by_id(folder_id)

    async def update(self, folder: FolderNode):
        return await self.repos.folder_repo.update(folder)

    async def delete(self, folder_key: str):
        return await self.repos.folder_repo.delete(folder_key)

    async def add_child(self, parent_folder_id: str, child_id: str, child_type: Literal["folder", "file"]):
        return await self.repos.folder_repo.move_item(parent_folder_id, child_id, child_type)

    async def get_children(self, folder_id: str, exclude_types: list[str] = []):
        return await self.repos.folder_repo.get_children(folder_id, exclude_types)

    async def create_batch(self, folders: List[FolderNode]):
        return await self.repos.folder_repo.create(folders)

    async def update_batch(self, folders: List[FolderNode]):
        return await self.repos.folder_repo.update_batch(folders)

    async def get_all_folders(self):
        return await self.repos.folder_repo.get_all_folders()

    async def move_batch(self, move_action: List[Tuple[str, str, str]]):
        return await self.repos.folder_repo.move_batch(move_action)
