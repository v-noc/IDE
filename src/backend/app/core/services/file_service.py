from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import FileNode
from typing import Optional


class FileService(ContainerService):
    def __init__(self, repos: Repositories):
        super().__init__(repos)

    async def create(self, name: str, qname: str, description: str, path: str, hash: str):
        file = FileNode(
            name=name,
            qname=qname,
            description=description,
            path=path,
            hash=hash,
        )
        return await self.repos.file_repo.create(file)

    async def write_code_by_id(self, node_key: str, code_block: str):
        """Wrapper for generic write_code in base class."""
        return await self.write_code(f"nodes/{node_key}", code_block)

    async def get(self, file_id: str):
        return await self.repos.file_repo.get_by_id(file_id)

    async def update(self, file: FileNode):
        return await self.repos.file_repo.update(file.key, file)

    async def delete(self, file_key: str):
        return await self.delete_recursive(file_key)

    async def add_function(self, file_id: str, function_id: str):
        return await self.add_child_to_container(file_id, function_id)

    async def add_call(self, file_id: str, call_id: str):
        return await self.add_child_to_container(file_id, call_id)

    async def add_class(self, file_id: str, class_id: str):
        return await self.add_child_to_container(file_id, class_id)

    async def get_children(self, file_id: str):
        return await self.repos.file_repo.get_containment_tree(file_id)

