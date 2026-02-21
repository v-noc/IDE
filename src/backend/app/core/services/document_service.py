import uuid
from app.core.repository import Repositories
from app.core.model.nodes import DocumentNode
from app.core.model.nodes import ProjectNode
from typing import List, Optional


class DocumentService:
    def __init__(self, repos: Repositories, project: ProjectNode):
        self.repos = repos
        self.project = project

    async def get(self, document_id, branch_name: Optional[str] = None):
        return await self.repos.document_repo.get_by_id(document_id, self.project.db_name, branch_name=branch_name)

    async def get_nodes_by_parent_node(self, node_id: str) -> List[DocumentNode]:
        return await self.repos.document_repo.get_by_parent_node(node_id, self.project.db_name)

    async def create(self,
                     name: str,
                     description: str,
                     node_id: str,
                     branch_name: Optional[str] = None,
                     ):

        document = DocumentNode(
            id=f"DocumentSchema/{str(uuid.uuid4())}",
            name=name,
            description=description,
            data="",
        )

        # node = await self.repos.nodes.get_by_key(node_id)
        # if not node:
        #     raise ValueError(f"Node {node_id} not found")

        created = await self.repos.document_repo.create_nodes(document, self.project.db_name, singular_name="document", plural_name="documents", branch_name=branch_name)

        if created:
            print("adding to parent node", document.id, node_id)
            await self.repos.document_repo.add_to_parent_node(document.id, node_id, self.project.db_name, branch_name=branch_name)

        return created

    async def update(self, document: DocumentNode, branch_name: Optional[str] = None):
        return await self.repos.document_repo.update(document, self.project.db_name, branch_name=branch_name)

    async def delete(self, document_id: str, branch_name: Optional[str] = None):
        return await self.repos.document_repo.delete(document_id, self.project.db_name, branch_name=branch_name)
