"""SubTask documents under a task."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from app.agent.models.task import SubTask, SubTaskState
from app.core.model.conversation_nodes import SubTaskNode, TaskNode
from app.core.model.schemas.conversation_schema import (
    SubTaskSchema,
    TaskSchema,
)
from app.db.async_terminus_client import WOQLQuery as WQ

from ._common import new_doc_id, utcnow

if TYPE_CHECKING:
    from app.db.async_terminus_client import AsyncClient


class SubtasksMixin:
    client: "AsyncClient"

    async def append_subtask(
        self, task_id: str, subtask: SubTask
    ) -> str | None:
        try:
            task_raw = await self.client.get_document(task_id)
        except Exception as exc:
            print(exc)
            return None
        if not task_raw:
            return None
        task_node = TaskNode.from_raw_dict(task_raw)
        now = utcnow()
        seq = task_node.sub_task_count
        sub_id = subtask.id or new_doc_id("SubTaskSchema")
        st = subtask.state
        state_val = st.value if isinstance(st, SubTaskState) else str(st)
        sub_node = SubTaskNode(
            id=sub_id,
            task_id=task_id,
            name=subtask.name,
            description=subtask.description,
            state=state_val,
            sequence=seq,
            started_at=subtask.started_at,
            finished_at=subtask.finished_at,
            error=subtask.error,
            touched_node_ids_json=json.dumps(subtask.touched_node_ids),
            created_at=now,
            updated_at=now,
        )

        try:
            await self.client.insert_document(
                SubTaskSchema.from_pydantic(sub_node),
                commit_msg=f"Subtask on {task_id}",
            )
        except Exception as exc:
            print(exc)
            return None

        task_node.sub_task_count = seq + 1
        task_node.updated_at = now
        try:
            await self.client.update_document(
                TaskSchema.from_pydantic(task_node),
                commit_msg=f"Bump sub_task_count {task_id}",
            )
        except Exception as exc:
            print(exc)
            return None
        return sub_id

    async def update_subtask(self, subtask_id: str, **fields: Any) -> bool:
        try:
            raw = await self.client.get_document(subtask_id)
        except Exception as exc:
            print(exc)
            return False
        if not raw:
            return False
        node = SubTaskNode.from_raw_dict(raw)

        if "name" in fields:
            node.name = fields["name"]
        if "description" in fields:
            node.description = fields["description"]
        if "state" in fields:
            st = fields["state"]
            node.state = st.value if hasattr(st, "value") else str(st)
        if "sequence" in fields:
            node.sequence = int(fields["sequence"])
        if "started_at" in fields:
            node.started_at = fields["started_at"]
        if "finished_at" in fields:
            node.finished_at = fields["finished_at"]
        if "error" in fields:
            node.error = fields["error"]
        if "touched_node_ids" in fields:
            node.touched_node_ids_json = json.dumps(fields["touched_node_ids"])

        node.updated_at = utcnow()

        try:
            await self.client.update_document(
                SubTaskSchema.from_pydantic(node),
                commit_msg=f"Update subtask {subtask_id}",
            )
        except Exception as exc:
            print(exc)
            return False
        return True

    async def get_subtasks(
        self,
        task_id: str,
        cursor: int = 0,
        limit: int = 50,
    ) -> list[SubTask]:
        cursor = max(0, int(cursor))
        cap = max(1, int(limit))
        try:
            filtered = WQ().woql_and(
                WQ().triple("v:st", "task", task_id),
                WQ().triple("v:st", "rdf:type", "@schema:SubTaskSchema"),
                WQ().triple("v:st", "sequence", "v:seq"),
                WQ().greater("v:seq", WQ().literal(cursor - 1, "xsd:integer")),
            )
            ordered = WQ().order_by("v:seq", order="asc").limit(cap, filtered)
            query = WQ().select("v:st_doc").woql_and(
                ordered,
                WQ().read_document("v:st", "v:st_doc"),
            )
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return []

        out: list[SubTask] = []
        for row in result.get("bindings", []):
            raw = row.get("st_doc")
            if not raw:
                continue
            n = SubTaskNode.from_raw_dict(raw)
            touched: list[str] = []
            try:
                touched = json.loads(n.touched_node_ids_json or "[]")
            except json.JSONDecodeError:
                touched = []
            out.append(
                SubTask(
                    id=n.id,
                    name=n.name,
                    description=n.description,
                    state=SubTaskState(n.state),
                    sequence=n.sequence,
                    started_at=n.started_at,
                    finished_at=n.finished_at,
                    error=n.error,
                    touched_node_ids=touched,
                )
            )
        return out
