from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import TypeAdapter

from app.agent.models.conversation import (
    Conversation,
    ConversationMessage,
    ConversationSummary,
    MessagePart,
    MessageRole,
)
from app.agent.models.task import SubTask, SubTaskState, Task, TaskState
from app.core.model.conversation_nodes import (
    ConversationNode,
    MessageNode,
    SubTaskNode,
    TaskNode,
)
from app.core.model.schemas.conversation_schema import (
    ConversationSchema,
    MessageSchema,
    SubTaskSchema,
    TaskSchema,
)
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ

_MESSAGE_PARTS_JSON = TypeAdapter(list[MessagePart])

_TERMINAL_TASK_STATES = frozenset(
    {TaskState.COMPLETED.value, TaskState.FAILED.value, TaskState.CANCELLED.value}
)


def _new_doc_id(class_name: str) -> str:
    return f"{class_name}/{uuid.uuid4()}"


class ConversationRepo:
    """TerminusDB persistence for conversations, messages, tasks, and subtasks."""

    def __init__(self, client: AsyncClient):
        self.client = client

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parts_to_json(parts: list[MessagePart]) -> str:
        return _MESSAGE_PARTS_JSON.dump_json(parts).decode("utf-8")

    @staticmethod
    def _parts_from_json(parts_json: str) -> list[MessagePart]:
        return _MESSAGE_PARTS_JSON.validate_json(parts_json.encode("utf-8"))

    async def create_conversation(
        self,
        title: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> str:
        now = self._utcnow()
        conv_id = _new_doc_id("ConversationSchema")
        node = ConversationNode(
            id=conv_id,
            name=title,
            description=description,
            metadata_json=json.dumps(metadata or {}),
            message_count=0,
            has_active_task=False,
            created_at=now,
            updated_at=now,
        )
        try:
            await self.client.insert_document(
                ConversationSchema.from_pydantic(node),
                commit_msg=f"Creating conversation {title!r}",
            )
        except Exception as exc:
            print(exc)
            return None
        return conv_id

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None:
            return None
        messages = await self.get_messages(conversation_id, cursor=0, limit=10_000)
        meta: dict[str, Any] = {}
        try:
            meta = json.loads(conv.metadata_json or "{}")
        except json.JSONDecodeError:
            meta = {}
        return Conversation(
            id=conv.id,
            title=conv.name,
            description=conv.description,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=conv.message_count,
            has_active_task=conv.has_active_task,
            messages=messages,
            metadata=meta,
        )

    async def _get_conversation_node(self, conversation_id: str) -> ConversationNode | None:
        try:
            raw = await self.client.get_document(conversation_id)
        except Exception as exc:
            print(exc)
            return None
        if not raw or "ConversationSchema" not in str(raw.get("@type", "")):
            return None
        return ConversationNode.from_raw_dict(raw)

    async def list_conversations(
        self,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[ConversationSummary]:
        try:
            items_raw = await self.client.get_all_documents(doc_type="ConversationSchema")
        except Exception as exc:
            print(exc)
            return []
        nodes = [ConversationNode.from_raw_dict(r) for r in items_raw]
        nodes.sort(key=lambda n: n.updated_at, reverse=True)
        if cursor:
            idx = next((i for i, n in enumerate(nodes) if n.id == cursor), None)
            if idx is not None:
                nodes = nodes[idx + 1 :]
        cap = max(1, limit)
        return [
            ConversationSummary(
                id=n.id,
                title=n.name,
                description=n.description,
                created_at=n.created_at,
                updated_at=n.updated_at,
                message_count=n.message_count,
                has_active_task=n.has_active_task,
            )
            for n in nodes[:cap]
        ]

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> str | None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None:
            return None
        now = self._utcnow()
        seq = conv.message_count
        msg_id = message.id or _new_doc_id("MessageSchema")
        role_val = message.role.value if isinstance(message.role, MessageRole) else str(
            message.role
        )
        msg_node = MessageNode(
            id=msg_id,
            conversation_id=conversation_id,
            role=role_val,
            parts_json=self._parts_to_json(message.parts),
            token_count=message.token_count,
            model_name=message.model,
            sequence=seq,
            created_at=message.created_at or now,
            updated_at=now,
        )
        try:
            await self.client.insert_document(
                MessageSchema.from_pydantic(msg_node),
                commit_msg=f"Message in {conversation_id}",
            )
        except Exception as exc:
            print(exc)
            return None

        conv.message_count = seq + 1
        conv.updated_at = now
        try:
            await self.client.update_document(
                ConversationSchema.from_pydantic(conv),
                commit_msg=f"Bump message_count {conversation_id}",
            )
        except Exception as exc:
            print(exc)
            return None
        return msg_id

    async def get_messages(
        self,
        conversation_id: str,
        cursor: int = 0,
        limit: int = 50,
    ) -> list[ConversationMessage]:
        cursor = max(0, int(cursor))
        cap = max(1, int(limit))
        try:
            filtered = WQ().woql_and(
                WQ().triple("v:msg", "conversation", conversation_id),
                WQ().triple("v:msg", "rdf:type", "@schema:MessageSchema"),
                WQ().triple("v:msg", "sequence", "v:seq"),
                WQ().greater("v:seq", WQ().literal(cursor - 1, "xsd:integer")),
            )
            ordered = WQ().order_by("v:seq", order="asc").limit(cap, filtered)
            query = WQ().select("v:msg_doc").woql_and(
                ordered,
                WQ().read_document("v:msg", "v:msg_doc"),
            )
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return []

        out: list[ConversationMessage] = []
        for row in result.get("bindings", []):
            raw = row.get("msg_doc")
            if not raw:
                continue
            node = MessageNode.from_raw_dict(raw)
            parts = self._parts_from_json(node.parts_json)
            out.append(
                ConversationMessage(
                    id=node.id,
                    role=MessageRole(node.role),
                    parts=parts,
                    sequence=node.sequence,
                    created_at=node.created_at,
                    token_count=node.token_count,
                    model=node.model_name,
                )
            )
        return out

    async def get_message(self, message_id: str) -> ConversationMessage | None:
        try:
            raw = await self.client.get_document(message_id)
        except Exception as exc:
            print(exc)
            return None
        if not raw or "MessageSchema" not in (raw.get("@type") or ""):
            return None
        node = MessageNode.from_raw_dict(raw)
        parts = self._parts_from_json(node.parts_json)
        return ConversationMessage(
            id=node.id,
            role=MessageRole(node.role),
            parts=parts,
            sequence=node.sequence,
            created_at=node.created_at,
            token_count=node.token_count,
            model=node.model_name,
        )

    async def create_task(
        self,
        conversation_id: str,
        message_id: str,
        task: Task,
    ) -> str | None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None:
            return None
        now = self._utcnow()
        task_id = task.id or _new_doc_id("TaskSchema")
        task.conversation_id = conversation_id
        task.message_id = message_id
        task.created_at = task.created_at or now
        task.updated_at = now
        node = task.to_task_node(task_id)
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
        node = TaskNode.from_raw_dict(raw)
        conv_id = node.conversation_id

        if "name" in fields:
            node.name = fields["name"]
        if "description" in fields:
            node.description = fields["description"]
        if "state" in fields:
            st = fields["state"]
            node.state = st.value if isinstance(st, TaskState) else str(st)
        if "progress" in fields:
            node.progress = float(fields["progress"])
        if "progress_message" in fields:
            node.progress_message = fields["progress_message"]
        if "workflow_name" in fields:
            node.workflow_name = fields["workflow_name"]
        if "workflow_params" in fields:
            wp = fields["workflow_params"]
            node.workflow_params_json = json.dumps(wp) if wp is not None else None
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

        node.updated_at = self._utcnow()

        try:
            await self.client.update_document(
                TaskSchema.from_pydantic(node),
                commit_msg=f"Update task {task_id}",
            )
        except Exception as exc:
            print(exc)
            return False

        if node.state in _TERMINAL_TASK_STATES and conv_id:
            await self._maybe_clear_active_task(conv_id)
        return True

    async def _maybe_clear_active_task(self, conversation_id: str) -> None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None or not conv.has_active_task:
            return
        try:
            open_tasks = await self._query_tasks_for_conversation(
                conversation_id,
                states=list(
                    {
                        TaskState.PENDING.value,
                        TaskState.RUNNING.value,
                    }
                ),
            )
        except Exception as exc:
            print(exc)
            return
        if open_tasks:
            return
        conv.has_active_task = False
        conv.updated_at = self._utcnow()
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
    ) -> list[TaskNode]:
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
        out: list[TaskNode] = []
        for row in result.get("bindings", []):
            raw = row.get("task_doc")
            if raw:
                out.append(TaskNode.from_raw_dict(raw))
        return out

    async def get_task(self, task_id: str) -> Task | None:
        try:
            raw = await self.client.get_document(task_id)
        except Exception as exc:
            print(exc)
            return None
        if not raw:
            return None
        node = TaskNode.from_raw_dict(raw)
        return Task.from_task_node(node)

    async def append_subtask(self, task_id: str, subtask: SubTask) -> str | None:
        try:
            task_raw = await self.client.get_document(task_id)
        except Exception as exc:
            print(exc)
            return None
        if not task_raw:
            return None
        task_node = TaskNode.from_raw_dict(task_raw)
        now = self._utcnow()
        seq = task_node.sub_task_count
        sub_id = subtask.id or _new_doc_id("SubTaskSchema")
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

        node.updated_at = self._utcnow()

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
