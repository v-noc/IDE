from typing import List
from terminusdb_client.woqlquery.woql_query import Doc

from app.db.async_terminus_client import AsyncClient
from app.core.model.schemas.test_schema import TestSchema, TestCaseSchema
from app.db.async_terminus_client import WOQLQuery as WQ


class TestRepo:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def get(self, id: str):
        try:
            item_raw = await self.client.get_document(id)
        except Exception as exc:
            print(exc)
            return None
        return item_raw

    async def get_by_ids(self, ids: List[str]):
        try:
            items_raw = await self.client.get_documents(ids)
        except Exception as exc:
            print(exc)
            return []
        return items_raw

    async def update(self, test: TestSchema):
        return await self.client.update(test)

    async def get_test_case_for_node(self, item_id: str):
        query = WQ().select("v:test_case_doc", "v:test_link_doc").woql_and(
            WQ().eq("v:item", item_id).
            path("v:item_link", "(owner_function|owner_class|owner_file)", "v:item").
            triple("v:test_case", "test_links", "v:item_link").
            read_document("v:test_case", "v:test_case_doc").
            read_document("v:test_link", "v:test_link_doc")
        )

    async def flush_batch(self, inserts, updates, deletes, ):
        queries = []
        for n in inserts:
            schema = TestCaseSchema.from_pydantic(n)._obj_to_dict()[0]
            queries.append(WQ().insert_document(Doc(schema)))

        for n in updates:
            schema = TestCaseSchema.from_pydantic(n)._obj_to_dict()[0]
            queries.append(WQ().update_document(Doc(schema)))

        for n in deletes:
            queries.append(WQ().delete_document(n))

        return await self.client.query(WQ().woql_and(*queries))
