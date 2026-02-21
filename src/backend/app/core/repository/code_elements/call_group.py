from typing import Literal, Optional
from app.core.repository.base_repo import BaseRepo, WQ
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import CallGroupNode
from app.core.model.schemas import CallGroupSchema
from app.core.repository.utils import CODE_CHILD_TYPE_TO_FIELD


class CallGroupRepo(BaseRepo[CallGroupNode, CallGroupSchema]):
    def __init__(self, client: AsyncClient):
        self.client = client

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal["call", "call_group"],
        project_db_name: str,
        branch_name: Optional[str] = None,
    ):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            item_type,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
            branch_name=branch_name,
        )

    async def delete(self, code_element_group_id: str, project_db_name: str, branch_name: Optional[str] = None):
        query = WQ().woql_and(
            WQ().opt(
                WQ().triple("v:parent", "call_group", code_element_group_id).opt(

                    WQ().eq("v:current", code_element_group_id).woql_and(
                        WQ().opt(
                            WQ().triple("v:current", "call_children", "v:child").
                            delete_triple("v:current", "call_children", "v:child").
                            add_triple(
                                "v:parent", "call_children", "v:child")
                        ),
                        WQ().opt(
                            WQ().triple("v:current", "call_group", "v:child").
                            delete_triple("v:current", "call_group", "v:child").
                            add_triple(
                                "v:parent", "call_group", "v:child")
                        )
                    ),

                    WQ().delete_triple(
                        "v:parent", "call_group", code_element_group_id)
                )
            ),
            WQ().delete_document(code_element_group_id),
        )
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.query(query, commit_msg=f"Deleting code_element_group {code_element_group_id}")
            except Exception as exc:
                print(exc)
                return False
        return True
