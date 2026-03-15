from typing import Optional

from app.core.model.schemas.code_element_schema import PlayGroundSchema
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ


class PlayGroundRepo:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, playground: PlayGroundSchema) -> bool:
        try:
            await self.client.insert_document(
                playground,
                commit_msg=f"Creating playground {playground._id}",
            )
            return True
        except Exception as exc:
            print(exc)
            return False

    async def get_by_id(self, playground_id: str) -> Optional[dict]:
        try:
            return await self.client.get_document(playground_id)
        except Exception as exc:
            print(exc)
            return None

    async def update(self, playground: PlayGroundSchema) -> bool:
        try:
            await self.client.update_document(
                playground,
                commit_msg=f"Updating playground {playground._id}",
            )
            return True
        except Exception as exc:
            print(exc)
            return False

    async def delete(self, playground_id: str) -> bool:
        try:
            await self.client.delete_document(
                playground_id,
                commit_msg=f"Deleting playground {playground_id}",
            )
            return True
        except Exception as exc:
            print(exc)
            return False

    async def get_by_owner_field(
        self, owner_field: str, owner_id: str
    ) -> list[dict]:
        query = (
            WQ()
            .select("v:playground_doc")
            .woql_and(
                WQ().triple("v:playground", owner_field, owner_id),
                WQ().read_document("v:playground", "v:playground_doc"),
            )
        )
        try:
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return []

        return [row["playground_doc"] for row in result.get("bindings", [])]

    async def get_by_owner_function_id(
        self, owner_function_id: str
    ) -> list[dict]:
        return await self.get_by_owner_field("owner_function", owner_function_id)

    async def get_by_owner_class_id(self, owner_class_id: str) -> list[dict]:
        return await self.get_by_owner_field("owner_class", owner_class_id)

    async def get_by_owner_file_id(self, owner_file_id: str) -> list[dict]:
        return await self.get_by_owner_field("owner_file", owner_file_id)

    async def get_by_owner_folder_id(self, owner_folder_id: str) -> list[dict]:
        return await self.get_by_owner_field("owner_folder", owner_folder_id)
