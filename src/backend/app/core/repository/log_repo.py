

from typing import List, Tuple, Optional

from terminusdb_client.woqlquery.woql_query import Doc
from app.db.async_terminus_client import AsyncClient
from app.core.repository.base_repo import BaseRepo
from app.core.model.logs import LogNode
from app.core.model.schemas import LogSchema
from app.db.async_terminus_client import WOQLQuery as WQ


class LogRepository():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create_batch(self, logs: List[LogNode]):

        try:
            raw_dict_batch = []

            for log in logs:
                raw_dict_batch.append(log.to_raw_dict())

            await self.client.insert_document(raw_dict_batch, commit_msg=f"Creating {len(logs)} logs")

        except Exception as exc:
            print(exc)
            return False
        return True

    async def get_function_log(self, function_id: str):

        try:
            query = WQ().select("v:log_doc").woql_and(
                WQ().eq("v:function", function_id).
                path("v:log", "origin_function", "v:function")
                .path("v:log", "(children_logs)*", "v:child_log")
                .read_document("v:child_log", "v:log_doc")
            )
            result = await self.client.query(query)

            return [LogNode.from_raw_dict(row["log_doc"]) for row in result["bindings"]]
        except Exception as exc:
            print(exc)
            return []

    async def get_parent_log(self, log_id: str):

        try:
            query = WQ().select("v:parent_doc").woql_and(
                WQ().eq("v:log", log_id).
                path("v:parent", "children_logs", "v:log")
                .read_document("v:parent", "v:parent_doc")
            )
            result = await self.client.query(query)

            if len(result["bindings"]) == 0:
                return None
            return LogNode.from_raw_dict(result["bindings"][0]["parent_doc"])
        except Exception as exc:
            print(exc)
            return None

    async def flush_batch_logs(self, inserts: List[LogNode], moves: List[Tuple[str, str, str]]):
        if not inserts and not moves:
            return True

        queries = []

        for log in inserts:

            queries.append(WQ().insert_document(
                Doc(LogSchema.from_pydantic(log)._obj_to_dict(True)[0])))

        for move in moves:
            queries.append(WQ().add_triple(move[1], "children_logs", move[0]))
        try:
            return await self.client.query(WQ().woql_and(*queries), commit_msg=f"Flushing {len(inserts)} logs and {len(moves)} moves")
        except Exception as exc:
            print(exc)
            return False
