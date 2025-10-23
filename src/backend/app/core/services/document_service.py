from app.core.repository import Repositories
from app.core.model.documents import DocumentNode
from typing import List


class DocumentService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def get(self, document_id):
        return self.repos.document_repo.get_by_key(document_id)

    def get_nodes_by_parent_node(self, node_id: str) -> List[DocumentNode]:
        # Use repository AQL to avoid N+1 lookups
        node = self.repos.nodes.get_by_key(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        return self.repos.document_repo.get_documents_for_node(node.id)

    def create(self,
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
        node = self.repos.nodes.get_by_key(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        created = self.repos.document_repo.create(document)
        node = self.repos.nodes.get_by_key(node_id)

        if not node:
            raise ValueError(f"Node {node_id} not found")

        else:
            node.documents.append(created.id)
            self.repos.nodes.update(node.key, node)

        return created

    def update(self, document: DocumentNode):
        return self.repos.document_repo.update(document.key, document)

    def delete(self, document_id: str, node_id: str):
        node = self.repos.nodes.get_by_key(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        node.documents.remove(document_id)
        self.repos.nodes.update(node.key, node)
        return self.repos.document_repo.delete(document_id)
