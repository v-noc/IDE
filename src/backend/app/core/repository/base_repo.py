from app.db.async_terminus_client import AsyncClient
from app.core.model.schemas import BaseSchema
from app.core.model.nodes import BaseNode


class BaseRepo[T: BaseSchema, N: BaseNode]:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, document: BaseSchema, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        document_schema = DocumentSchema.from_pydantic(document)
        await self.client.insert_document(document_schema, commit_msg=f"Creating document {document.id}")
        if current_db:
            await self.client.set_db(current_db)
