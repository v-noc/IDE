

from typing import List, Tuple, Optional
from app.db.async_terminus_client import AsyncClient
from app.core.repository.base_repo import BaseRepo
from app.core.model.logs import LogNode
from app.core.model.schemas import LogSchema
from app.db.async_terminus_client import WOQLQuery as WQ


class LogRepository(BaseRepo[LogNode, LogSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, LogNode, LogSchema)

    async def create_batch(self, logs: List[LogNode], project_db_name: str, branch_name: Optional[str] = None):
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                raw_dict_batch = []

                for log in logs:
                    raw_dict_batch.append(log.to_raw_dict())

                await new_client.insert_document(raw_dict_batch, commit_msg=f"Creating {len(logs)} logs")

            except Exception as exc:
                print(exc)
                return False
        return True

    async def move_logs_to_parent_logs(self, moves: List[Tuple[str, str, str]], project_db_name: str, branch_name: Optional[str] = None):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field={"log": "children_logs"},
            project_db_name=project_db_name,
            branch_name=branch_name,
        )

    async def get_function_log(self, function_id: str, project_db_name: str, branch_name: Optional[str] = None):
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                query = WQ().select("v:log_doc").woql_and(
                    WQ().eq("v:function", function_id).
                    path("v:log", "origin_function", "v:function")
                    .path("v:log", "(children_logs)*", "v:child_log")
                    .read_document("v:child_log", "v:log_doc")
                )
                result = await new_client.query(query)

                return [LogNode.from_raw_dict(row["log_doc"]) for row in result["bindings"]]
            except Exception as exc:
                print(exc)
                return []

    async def get_parent_log(self, log_id: str, project_db_name: str, branch_name: Optional[str] = None):
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                query = WQ().select("v:parent_doc").woql_and(
                    WQ().eq("v:log", log_id).
                    path("v:parent", "children_logs", "v:log")
                    .read_document("v:parent", "v:parent_doc")
                )
                result = await new_client.query(query)
                if len(result["bindings"]) == 0:
                    return None
                return self._to_node(result["bindings"][0]["parent_doc"])
            except Exception as exc:
                print(exc)
                return None
