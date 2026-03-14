from typing import Dict, List, Sequence

from terminusdb_client.woqlquery.woql_query import Doc

from app.core.model.schemas.test_schema import TestCaseSchema, TestLinkSchema
from app.core.model.schemas.test_schema import TestConfigSchema
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ


class TestRepo:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def get(self, item_id: str):
        try:
            return await self.client.get_document(item_id)
        except Exception as exc:
            print(exc)
            return None

    async def get_by_ids(self, ids: List[str]):
        if not ids:
            return []
        try:
            return await self.client.get_documents(ids)
        except Exception as exc:
            print(exc)
            return []

    async def get_test_config(self, project_db_name: str):
        return await self.get(f"TestConfigSchema/{project_db_name}")

    async def upsert_test_config(self, config: TestConfigSchema) -> bool:
        try:
            await self.client.update_document(
                config,
                commit_msg=f"Upsert test config {config._id}",
            )
            return True
        except Exception as exc:
            print(f"Failed to upsert test config: {exc}")
            return False

    async def delete_test_config(self, project_db_name: str) -> bool:
        config_id = f"TestConfigSchema/{project_db_name}"
        try:
            await self.client.delete_document(
                config_id,
                commit_msg=f"Delete test config {config_id}",
            )
            return True
        except Exception as exc:
            print(f"Failed to delete test config: {exc}")
            return False

    async def get_test_cases_for_node(self, item_id: str):
        query = (
            WQ()
            .select("v:test_case_doc")
            .woql_and(
                WQ().woql_or(
                    WQ().woql_and(
                        WQ().triple("v:test_link", "owner_function", item_id),
                        WQ().triple("v:test_case", "test_links", "v:test_link"),
                    ),
                    WQ().woql_and(
                        WQ().triple("v:test_link", "owner_class", item_id),
                        WQ().triple("v:test_case", "test_links", "v:test_link"),
                    ),
                    WQ().woql_and(
                        WQ().triple("v:test_link", "owner_file", item_id),
                        WQ().triple("v:test_case", "test_links", "v:test_link"),
                    ),
                ),
                WQ().read_document("v:test_case", "v:test_case_doc"),
            )
        )
        try:
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return []
        return [row["test_case_doc"] for row in result.get("bindings", [])]

    @staticmethod
    def _to_query_documents(
        items: Sequence[TestCaseSchema | TestLinkSchema],
    ) -> list[dict]:
        return [item._obj_to_dict()[0] for item in items]

    async def flush_batch(
        self,
        test_cases: Sequence[TestCaseSchema],
        test_links: Sequence[TestLinkSchema],
    ) -> bool:
        """
        Diff existing test case links with the new run and apply inserts/updates/deletes
        in a single TerminusDB query.
        """
        if not test_cases and not test_links:
            return True

        existing_case_docs = await self.get_by_ids(
            [tc._id for tc in test_cases],
        )
        existing_case_by_id: Dict[str, dict] = {
            raw.get("@id"): raw for raw in existing_case_docs if raw.get("@id")
        }

        existing_link_ids: set[str] = set()
        for case_doc in existing_case_docs:
            existing_link_ids.update(
                case_doc.get("test_links", set()) or set())

        new_link_by_id = {link._id: link for link in test_links}
        new_link_ids = set(new_link_by_id.keys())

        link_inserts = [new_link_by_id[link_id]
                        for link_id in (new_link_ids - existing_link_ids)]
        link_updates = [new_link_by_id[link_id]
                        for link_id in (new_link_ids & existing_link_ids)]
        link_deletes = list(existing_link_ids - new_link_ids)

        case_inserts: list[TestCaseSchema] = []
        case_updates: list[TestCaseSchema] = []
        for case in test_cases:
            if case._id in existing_case_by_id:
                case_updates.append(case)
            else:
                case_inserts.append(case)

        queries = []
        insert_docs = self._to_query_documents(
            link_inserts,
        ) + self._to_query_documents(case_inserts)
        for raw in insert_docs:
            queries.append(WQ().insert_document(Doc(raw)))

        update_docs = self._to_query_documents(
            link_updates,
        ) + self._to_query_documents(case_updates)
        for raw in update_docs:
            queries.append(WQ().update_document(Doc(raw)))

        for link_id in link_deletes:
            queries.append(WQ().delete_document(link_id))

        if not queries:
            return True

        try:
            await self.client.query(
                WQ().woql_and(*queries),
                commit_msg=(
                    "Batch tests: "
                    f"cases(+{len(case_inserts)} ~{len(case_updates)}), "
                    "links("
                    f"+{len(link_inserts)} "
                    f"~{len(link_updates)} "
                    f"-{len(link_deletes)})"
                ),
            )
            return True
        except Exception as exc:
            print(f"Test batch operation failed: {exc}")
            return False
