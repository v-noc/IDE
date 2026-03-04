import uuid
from app.core.model.nodes import DocumentNode
from typing import List

from app.db.context import ProjectUoW


class DocumentService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow

    async def get(self, document_id, is_root: bool = False):
        if is_root:
            return await self.uow.get_meta_repos().document_repo.get_by_id(document_id)
        else:
            return await self.uow.get_project_repos().document_repo.get_by_id(document_id)

    async def get_nodes_by_parent_node(self, node_id: str) -> List[DocumentNode]:
        if node_id.startswith("ProjectSchema/"):
            return await self.uow.get_meta_repos().document_repo.get_by_parent_node(node_id)
        else:
            return await self.uow.get_project_repos().document_repo.get_by_parent_node(node_id)

    async def create(self,
                     name: str,
                     description: str,
                     node_id: str,
                     ):
        repos = self.uow.get_project_repos()
        if node_id.startswith("ProjectSchema/"):
            repos = self.uow.get_meta_repos()

        document = DocumentNode(
            id=f"DocumentSchema/{str(uuid.uuid4())}",
            name=name,
            description=description,
            data="",
        )

        created = await repos.document_repo.create_nodes(document, singular_name="document", plural_name="documents")

        if created:
            print("adding to parent node", document.id, node_id)
            await repos.document_repo.add_to_parent_node(document.id, node_id)

        return created

    async def update(self, document: DocumentNode, is_root: bool = False):
        repos = self.uow.get_project_repos()
        if is_root:
            repos = self.uow.get_meta_repos()

        return await repos.document_repo.update(document)

    async def delete(self, document_id: str, is_root: bool = False):
        repos = self.uow.get_project_repos()
        if is_root:
            repos = self.uow.get_meta_repos()
        return await repos.document_repo.delete(document_id)
