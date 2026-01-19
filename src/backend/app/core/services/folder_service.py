from app.core.repository import Repositories
from app.core.services.container_service import ContainerService
from app.core.model.nodes import FolderNode


class FolderService(ContainerService):
    def __init__(self, repos: Repositories):
        super().__init__(repos)

    async def create(self, name: str, qname: str, description: str, path: str):
        folder = FolderNode(
            name=name,
            qname=qname,
            description=description,
            path=path,
        )
        return await self.repos.folder_repo.create(folder)

    async def get(self, folder_id: str):
        return await self.repos.folder_repo.get_by_id(folder_id)

    async def update(self, folder: FolderNode):
        return await self.repos.folder_repo.update(folder.key, folder)

    async def delete(self, folder_key: str):
        return await self.delete_recursive(folder_key)

    async def add_folder(self, parent_folder_id: str, folder_id: str):
        return await self.add_child_to_container(parent_folder_id, folder_id)

    async def add_file(self, parent_folder_id: str, file_id: str):
        return await self.add_child_to_container(parent_folder_id, file_id)


    async def get_children(self, folder_id: str):
        return await self.repos.folder_repo.get_containment_tree(folder_id)
