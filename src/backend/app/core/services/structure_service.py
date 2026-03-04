from app.db.context import ProjectUoW
from app.core.model.nodes import FileNode, FolderNode
from app.core.model.schemas import FileSchema, FolderSchema
from typing import List, Tuple


class StructureService():
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()

    async def create(self, structure: FolderNode | FileNode):
        return await self.repos.structure_repo.create(structure)

    async def get(self, structure_id: str):
        return await self.repos.structure_repo.get_by_id(structure_id)

    async def update(self, structure: FolderNode | FileNode):
        return await self.repos.structure_repo.update(structure)

    async def delete(self, structure_id: str):
        return await self.repos.structure_repo.delete(structure_id)

    async def move_item(self, new_parent_id: str, item_id: str, child_type: str):
        return await self.repos.structure_repo.move_item(new_parent_id, item_id, child_type)

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.repos.structure_repo.move_batch(moves)

    async def get_all_folder(self):
        return await self.repos.structure_repo.get_all(doc_type=FolderSchema.__name__)

    async def get_all_file(self):
        return await self.repos.structure_repo.get_all(doc_type=FileSchema.__name__)

    async def update_batch(self, structures: List[FolderNode | FileNode]):
        return await self.repos.structure_repo.update_batch(structures)

    async def flush_batch(self, insert: List[FolderNode | FileNode], update: List[FolderNode | FileNode], delete: List[str], move: List[Tuple[str, str, str]]):
        return await self.repos.structure_repo.flush_batch(insert, update, delete, move)
