"""Task documents and conversation active-task flag."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from app.core.model.conversation_enums import TaskState
from app.core.model.conversation_nodes import Task, _coerce_task_state
from app.core.model.schemas.conversation_schema import (
    ConversationSchema,
    TaskSchema,
)
from app.db.async_terminus_client import WOQLQuery as WQ

from ._common import TERMINAL_TASK_STATES, new_doc_id, utcnow

if TYPE_CHECKING:
    from app.db.async_terminus_client import AsyncClient


class TasksMixin:
    client: "AsyncClient"

    async def create_task(
        self,
        conversation_id: str,
        message_id: str,
        task: Task,
    ) -> str | None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None:
            return None
        now = utcnow()
        task_id = task.id or new_doc_id("TaskSchema")
        node = task.model_copy(
            update={
                "id": task_id,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "created_at": task.created_at or now,
                "updated_at": now,
            }
        )
        try:
            await self.client.insert_document(
                TaskSchema.from_pydantic(node),
                commit_msg=f"Task for conversation {conversation_id}",
            )
        except Exception as exc:
            print(exc)
            return None

        conv.has_active_task = True
        conv.updated_at = now
        try:
            await self.client.update_document(
                ConversationSchema.from_pydantic(conv),
                commit_msg=f"Mark active task {conversation_id}",
            )
        except Exception as exc:
            print(exc)
            return None
        return task_id

    async def update_task(self, task_id: str, **fields: Any) -> bool:
        try:
            raw = await self.client.get_document(task_id)
        except Exception as exc:
            print(exc)
            return False
        if not raw:
            return False
        node = Task.from_raw_dict(raw)
        conv_id = node.conversation_id

        if "name" in fields:
            node.name = fields["name"]
        if "description" in fields:
            node.description = fields["description"]
        if "state" in fields:
            node.state = _coerce_task_state(fields["state"])
        if "progress" in fields:
            node.progress = float(fields["progress"])
        if "progress_message" in fields:
            node.progress_message = fields["progress_message"]
        if "workflow_name" in fields:
            node.workflow_name = fields["workflow_name"]
        if "workflow_params" in fields:
            wp = fields["workflow_params"]
            node.workflow_params_json = (
                json.dumps(wp) if wp is not None else None
            )
        if "started_at" in fields:
            node.started_at = fields["started_at"]
        if "finished_at" in fields:
            node.finished_at = fields["finished_at"]
        if "error" in fields:
            node.error = fields["error"]
        if "result" in fields:
            r = fields["result"]
            node.result_json = json.dumps(r) if r is not None else None
        if "sub_task_count" in fields:
            node.sub_task_count = int(fields["sub_task_count"])

        node.updated_at = utcnow()

        try:
            await self.client.update_document(
                TaskSchema.from_pydantic(node),
                commit_msg=f"Update task {task_id}",
            )
        except Exception as exc:
            print(exc)
            return False

        if node.state in TERMINAL_TASK_STATES and conv_id:
            await self._maybe_clear_active_task(conv_id)
        return True

    async def _maybe_clear_active_task(self, conversation_id: str) -> None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None or not conv.has_active_task:
            return
        try:
            open_tasks = await self._query_tasks_for_conversation(
                conversation_id,
                states=[
                    TaskState.PENDING.value,
                    TaskState.RUNNING.value,
                ],
            )
        except Exception as exc:
            print(exc)
            return
        if open_tasks:
            return
        conv.has_active_task = False
        conv.updated_at = utcnow()
        try:
            await self.client.update_document(
                ConversationSchema.from_pydantic(conv),
                commit_msg=f"Clear active task flag {conversation_id}",
            )
        except Exception as exc:
            print(exc)

    async def _query_tasks_for_conversation(
        self,
        conversation_id: str,
        states: list[str],
    ) -> list[Task]:
        if not states:
            return []
        query = (
            WQ()
            .select("v:task_doc")
            .woql_and(
                WQ().triple("v:task", "conversation", conversation_id),
                WQ().triple("v:task", "rdf:type", "@schema:TaskSchema"),
                WQ().triple("v:task", "state", "v:state"),
                WQ().member("v:state", [WQ().string(s) for s in states]),
                WQ().read_document("v:task", "v:task_doc"),
            )
        )
        try:
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return []
        out: list[Task] = []
        for row in result.get("bindings", []):
            raw = row.get("task_doc")
            if raw:
                out.append(Task.from_raw_dict(raw))
        return out

    async def get_task(self, task_id: str) -> Task | None:
        try:
            raw = await self.client.get_document(task_id)
        except Exception as exc:
            print(exc)
            return None
        if not raw:
            return None
        return Task.from_raw_dict(raw)
