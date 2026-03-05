
from typing import Optional
from app.db.async_terminus_client import AsyncClient
from app.core.repository.base_repo import BaseRepo
from app.core.model.nodes import DocumentNode
from app.core.model.schemas import DocumentSchema
from app.db.async_terminus_client import WOQLQuery as WQ


class DocumentRepo(BaseRepo[DocumentNode, DocumentSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, DocumentNode, DocumentSchema)

    async def get_by_parent_node(self, node_id: str):

        try:
            query = WQ().select("v:document_doc").woql_and(
                WQ().eq("v:node", node_id).
                triple("v:node", "documents", "v:document")
                .read_document("v:document", "v:document_doc")
            )
            result = await self.client.query(query)

            items_raw = [row["document_doc"] for row in result["bindings"]]
        except Exception as exc:
            print(exc)
            return []

        return [DocumentNode.from_raw_dict(item_raw) for item_raw in items_raw]

    async def add_to_parent_node(self, document_id: str, node_id: str):
        await self.move_item_by_type(node_id, document_id, "document", {"document": "documents"})

    async def update(self, document: DocumentNode):
        return await self.update_node(document, commit_msg=f"Updating document {document.id}")

    async def delete(self, document_id: str):
        await self.delete_with_parent_cleanup(document_id, "documents", f"Deleting document {document_id}")
