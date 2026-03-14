from datetime import datetime, timezone
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
            .select("v:test_case_doc", "v:test_link_doc")
            .woql_and(
                WQ().woql_or(
                    WQ().woql_and(
                        WQ().triple(
                            "v:test_link", "owner_function", item_id,
                        ),
                        WQ().triple(
                            "v:test_case", "test_links", "v:test_link",
                        ),

                    ),
                    WQ().woql_and(
                        WQ().triple("v:test_link", "owner_class", item_id),
                        WQ().triple(
                            "v:test_case", "test_links", "v:test_link",
                        ),
                    ),
                    WQ().woql_and(
                        WQ().triple("v:test_link", "owner_file", item_id),
                        WQ().triple(
                            "v:test_case", "test_links", "v:test_link",
                        ),
                    ),
                ),
                WQ().read_document("v:test_link", "v:test_link_doc"),
                WQ().read_document("v:test_case", "v:test_case_doc"),
            )
        )
        try:
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return []

        test_cases = [row["test_case_doc"]
                      for row in result.get("bindings", [])]
        link_ids: list[str] = []
        for case_doc in test_cases:
            for link_id in case_doc.get("test_links", set()) or set():
                link_ids.append(link_id)

        link_docs = await self.get_by_ids(list(set(link_ids)))
        link_doc_by_id = {
            doc.get("@id"): doc for doc in link_docs if doc.get("@id")
        }

        for case_doc in test_cases:
            hydrated_links = []
            for link_id in case_doc.get("test_links", set()) or set():
                hydrated_links.append(link_doc_by_id.get(link_id, link_id))
            case_doc["test_links"] = hydrated_links

        return test_cases

    @staticmethod
    def _to_query_documents(
        items: Sequence[TestCaseSchema | TestLinkSchema],
    ) -> list[dict]:
        return [item._obj_to_dict()[0] for item in items]

    async def flush_batch(
        self,
        case_inserts: Sequence[TestCaseSchema],
        case_updates: Sequence[TestCaseSchema],
        link_inserts: Sequence[TestLinkSchema],
        link_updates: Sequence[TestLinkSchema],
        link_deletes: Sequence[str],
        insert_link_parent: Dict[str, str],
        delete_link_parent: Dict[str, str],
    ) -> bool:
        if not (case_inserts or case_updates or link_inserts or link_updates or link_deletes):
            return True

        queries = []
        now = datetime.now(timezone.utc)

        # 1. Case Inserts (Disjoint from updates)
        for case in case_inserts:
            raw = case._obj_to_dict()[0]
            raw["test_links"] = []  # Added via triples later
            queries.append(WQ().insert_document(Doc(raw)))

        # 2. Link Inserts
        for link in link_inserts:
            raw = link._obj_to_dict()[0]
            queries.append(WQ().insert_document(Doc(raw)))
            parent_id = insert_link_parent.get(link._id)
            if parent_id:
                # opt() ensures we don't fail if the triple somehow exists
                queries.append(WQ().opt(WQ().add_triple(
                    parent_id, "test_links", link._id)))

        # 3. Link Updates (Handling the 'lines' set)
        for i, link in enumerate(link_updates):
            # Use unique variable names to avoid collisions in large batches
            var_line = f"v:old_line_{i}"
            queries.append(
                WQ().woql_and(
                    WQ().opt(
                        WQ().woql_and(
                            WQ().triple(link._id, "lines", var_line),
                            WQ().delete_triple(link._id, "lines", var_line)
                        )
                    ),
                    *[WQ().add_triple(link._id, "lines", line)
                      for line in sorted(link.lines)],
                    # Cleanly replace updated_at
                    WQ().opt(
                        WQ().woql_and(
                            WQ().triple(link._id, "updated_at",
                                        f"v:old_link_upd_{i}"),
                            WQ().delete_triple(
                                link._id, "updated_at", f"v:old_link_upd_{i}")
                        )
                    ),
                    WQ().add_triple(link._id, "updated_at", now)
                )
            )

        # 4. Case Updates (Functional Properties)
        for i, case in enumerate(case_updates):
            props = [("name", WQ().string(case.name)),
                     ("node_id", WQ().string(case.node_id)),
                     ("path", WQ().string(case.path)),
                     ("updated_at", now)]

            case_q = []
            for prop_name, new_val in props:
                v_old = f"v:old_{prop_name}_{i}"
                case_q.append(
                    WQ().woql_and(
                        WQ().opt(
                            WQ().woql_and(
                                WQ().triple(case._id, prop_name, v_old),
                                WQ().delete_triple(case._id, prop_name, v_old)
                            )
                        ),
                        WQ().add_triple(case._id, prop_name, new_val)
                    )
                )
            queries.append(WQ().woql_and(*case_q))

        # 5. Deletions
        for link_id in link_deletes:
            parent_id = delete_link_parent.get(link_id)
            if parent_id:
                queries.append(WQ().opt(WQ().delete_triple(
                    parent_id, "test_links", link_id)))
            queries.append(WQ().delete_document(link_id))

        try:
            await self.client.query(
                WQ().woql_and(*queries),
                commit_msg=f"Batch tests: {len(case_updates)} cases updated, {len(link_updates)} links updated"
            )
            return True
        except Exception as exc:
            print(f"Test batch operation failed: {exc}")
            return False
