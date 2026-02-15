from app.core.repository import Repositories
from app.core.model.nodes import FileNode, ProjectNode
from typing import Optional
from datetime import datetime, timezone


class FileService():
    def __init__(self, repos: Repositories, project: ProjectNode):
        self.repos = repos
        self.project = project

    async def create(self, id: str, name: str, qname: str, description: str, path: str, hash: str):
        file = FileNode(
            id=id,
            name=name,
            qname=qname,
            description=description,
            path=path,
            hash=hash,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return await self.repos.file_repo.create(file, self.project.db_name)

    async def write_code_by_id(self, node_key: str, code_block: str):
        """Wrapper for generic write_code in base class."""
        return await self.write_code(f"nodes/{node_key}", code_block)

    async def get(self, file_id: str):
        return await self.repos.file_repo.get_by_id(file_id, self.project.db_name)

    async def update(self, file: FileNode):
        return await self.repos.file_repo.update(file, self.project.db_name)

    async def delete(self, file_id: str):
        return await self.repos.file_repo.delete(file_id, self.project.db_name)

    async def add_function(self, file_id: str, function_id: str):
        return await self.add_child(file_id, function_id)

    async def add_call(self, file_id: str, call_id: str):
        return await self.add_child(file_id, call_id)

    async def add_class(self, file_id: str, class_id: str):
        return await self.add_child(file_id, class_id)

    async def get_children(self, file_id: str):
        return await self.repos.file_repo.get_containment_tree(file_id)

    async def get_all_files(self):
        return await self.repos.file_repo.get_all_files(self.project.db_name)
