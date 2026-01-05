from app.core.repository import Repositories
from app.core.model.documents import DocumentNode
from typing import List


class DocumentService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    async def get(self, document_id):
        return await self.repos.document_repo.get_by_key(document_id)

    async def get_nodes_by_parent_node(self, node_id: str) -> List[DocumentNode]:
        # Use repository AQL to avoid N+1 lookups
        node = await self.repos.nodes.get_by_key(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        return await self.repos.document_repo.get_documents_for_node(node.id)

    async def create(self,
                     name: str,
                     description: str,
                     node_id: str,
                     ):

        document = DocumentNode(
            name=name,
            description=description,
            data="",
            children=[],
        )
        node = await self.repos.nodes.get_by_key(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        created = await self.repos.document_repo.create(document)
        node = await self.repos.nodes.get_by_key(node_id)

        if not node:
            raise ValueError(f"Node {node_id} not found")

        else:
            node.documents.append(created.id)
            await self.repos.nodes.update(node.key, node)

        return created

    async def update(self, document: DocumentNode):
        return await self.repos.document_repo.update(document.key, document)

    async def delete(self, document_id: str, node_id: str):
        node = await self.repos.nodes.get_by_key(node_id)

        if not node:
            raise ValueError(f"Node {node_id} not found")
        document = await self.repos.document_repo.get_by_key(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        node.documents.remove(document.id)
        await self.repos.nodes.update(node.key, node)
        return await self.repos.document_repo.delete(document_id)
