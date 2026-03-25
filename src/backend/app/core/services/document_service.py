import uuid
from app.core.model.nodes import DocumentNode
from app.core.model.schemas.structure_schema import INIT_FOLDER_ID
from typing import List, Optional

from app.db.context import ProjectUoW


def _resolve_node_id(node_id: str, project_id: str | None) -> str:
    """Resolve project node id to FolderSchema/init (global document theme folder)."""
    if project_id and (node_id == project_id or node_id.startswith("ProjectSchema/")):
        return INIT_FOLDER_ID
    return node_id


class DocumentService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow

    async def get(self, document_id):
        return await self.uow.get_project_repos().document_repo.get_by_id(document_id)

    async def get_nodes_by_parent_node(self, node_id: str, compare_to: Optional[bool] = False) -> List[DocumentNode]:
        effective_id = _resolve_node_id(
            node_id, self.uow.project.id if self.uow.project else None)
        if compare_to:
            return await self.uow.get_project_repos(use_compare_to=True).document_repo.get_by_parent_node(effective_id)
        return await self.uow.get_project_repos().document_repo.get_by_parent_node(effective_id)

    async def create(self,
                     name: str,
                     description: str,
                     node_id: str,
                     ):
        repos = self.uow.get_project_repos()
        effective_id = _resolve_node_id(
            node_id, self.uow.project.id if self.uow.project else None)

        document = DocumentNode(
            id=f"DocumentSchema/{str(uuid.uuid4())}",
            name=name,
            description=description,
            data="",
            markdown="",
        )

        created = await repos.document_repo.create_nodes(document, singular_name="document", plural_name="documents")

        if created:
            await repos.document_repo.add_to_parent_node(document.id, effective_id)

        return created

    async def update(self, document: DocumentNode):
        return await self.uow.get_project_repos().document_repo.update(document)

    async def delete(self, document_id: str):
        return await self.uow.get_project_repos().document_repo.delete(document_id)
