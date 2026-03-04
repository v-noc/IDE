import aiofiles

from app.core.model.nodes import FileNode
from app.core.utils.code_utils import build_abs_file_path, extract_code_from_file
from typing import List, Tuple
from datetime import datetime, timezone
from app.db.context import ProjectUoW


class FileService():
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()

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
        return await self.repos.file_repo.create(file)

    async def create_batch(self, file_nodes: List[FileNode]):
        return await self.repos.file_repo.create(file_nodes)

    async def update_batch(self, file_nodes: List[FileNode]):
        return await self.repos.file_repo.update_batch(file_nodes)

    async def move_batch(self, file_moves: List[Tuple[str, str, str]]):
        return await self.repos.file_repo.move_batch(file_moves)

    async def write_code_by_id(self, node_key: str, code_block: str):
        """Wrapper for generic write_code in base class."""
        return await self.write_code(f"nodes/{node_key}", code_block)

    async def get(self, file_id: str):
        return await self.repos.file_repo.get_by_id(file_id)

    async def update(self, file: FileNode):
        return await self.repos.file_repo.update(file)

    async def delete(self, file_id: str):
        return await self.repos.file_repo.delete(file_id)

    async def add_function(self, file_id: str, function_id: str):
        return await self.repos.file_repo.move_item(file_id, function_id, "function")

    async def add_call(self, file_id: str, call_id: str):
        return await self.repos.file_repo.move_item(file_id, call_id, "call")

    async def add_class(self, file_id: str, class_id: str):
        return await self.repos.file_repo.move_item(file_id, class_id, "class")

    async def get_children(self, file_id: str):
        return await self.repos.file_repo.get_children(file_id, [])

    async def get_all_files(self):
        return await self.repos.file_repo.get_all_files()

    async def get_parent_file(self, file_id: str):
        return await self.repos.file_repo.get_parent_file(file_id)

    async def get_code(self, file_id: str):
        file_node = await self.get(file_id)
        if not file_node:
            return None

        abs_path = build_abs_file_path(self.uow.project.path, file_node.path)
        code = await extract_code_from_file(abs_path, None)

        return {
            "id": file_node.id,
            "name": file_node.name,
            "qname": file_node.qname,
            "file_path": file_node.path,
            "file_name": file_node.name,
            "code": code,
        }

    async def write_code(self, file_id: str, code_block: str) -> dict:
        """Write entire file content. Returns {success: bool, error?: str}."""
        file_node = await self.get(file_id)
        if not file_node:
            return {"success": False, "error": "File not found"}

        abs_path = build_abs_file_path(self.uow.project.path, file_node.path)
        try:
            async with aiofiles.open(abs_path, "w", encoding="utf-8") as f:
                await f.write(code_block)
            return {"success": True}
        except IOError as e:
            return {"success": False, "error": str(e)}
