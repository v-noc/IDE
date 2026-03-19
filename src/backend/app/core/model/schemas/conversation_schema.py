from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.core.model.conversation_nodes import (
    ConversationNode,
    MessageNode,
    SubTaskNode,
    TaskNode,
)
from .base import BaseSchema, TerminusBase


class ConversationSchema(BaseSchema):
    """Root conversation document; messages point here via `conversation` edge."""

    metadata_json: str
    message_count: int
    has_active_task: bool

    @staticmethod
    def from_pydantic(node: ConversationNode) -> "ConversationSchema":
        return ConversationSchema(
            _id=node.id,
            name=node.name,
            description=node.description,
            metadata_json=node.metadata_json,
            message_count=node.message_count,
            has_active_task=node.has_active_task,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def to_pydantic(self) -> ConversationNode:
        return ConversationNode(
            id=self._id,
            name=self.name,
            description=self.description,
            metadata_json=self.metadata_json or "{}",
            message_count=int(self.message_count or 0),
            has_active_task=bool(self.has_active_task),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class MessageSchema(TerminusBase):
    conversation: "ConversationSchema"
    role: str
    parts_json: str
    token_count: Optional[int]
    model_name: Optional[str]
    sequence: int

    @staticmethod
    def from_pydantic(node: MessageNode) -> "MessageSchema":
        return MessageSchema(
            _id=node.id,
            conversation=node.conversation_id,
            role=node.role,
            parts_json=node.parts_json,
            token_count=node.token_count,
            model_name=node.model_name,
            sequence=node.sequence,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def to_pydantic(self) -> MessageNode:
        conv = self.conversation
        conv_id = conv if isinstance(conv, str) else getattr(conv, "_id", "")
        return MessageNode(
            id=self._id,
            conversation_id=conv_id,
            role=self.role,
            parts_json=self.parts_json or "[]",
            token_count=self.token_count,
            model_name=self.model_name,
            sequence=int(self.sequence or 0),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class TaskSchema(BaseSchema):
    conversation: "ConversationSchema"
    message: "MessageSchema"
    state: str
    progress: float
    progress_message: str
    workflow_name: Optional[str]
    workflow_params_json: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error: Optional[str]
    result_json: Optional[str]
    sub_task_count: int

    @staticmethod
    def from_pydantic(node: TaskNode) -> "TaskSchema":
        return TaskSchema(
            _id=node.id,
            name=node.name,
            description=node.description,
            conversation=node.conversation_id,
            message=node.message_id,
            state=node.state,
            progress=node.progress,
            progress_message=node.progress_message,
            workflow_name=node.workflow_name,
            workflow_params_json=node.workflow_params_json,
            started_at=node.started_at,
            finished_at=node.finished_at,
            error=node.error,
            result_json=node.result_json,
            sub_task_count=node.sub_task_count,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def to_pydantic(self) -> TaskNode:
        conv = self.conversation
        msg = self.message
        return TaskNode(
            id=self._id,
            name=self.name,
            description=self.description,
            conversation_id=conv if isinstance(conv, str) else getattr(conv, "_id", ""),
            message_id=msg if isinstance(msg, str) else getattr(msg, "_id", ""),
            state=self.state,
            progress=float(self.progress or 0.0),
            progress_message=self.progress_message or "",
            workflow_name=self.workflow_name,
            workflow_params_json=self.workflow_params_json,
            started_at=self.started_at,
            finished_at=self.finished_at,
            error=self.error,
            result_json=self.result_json,
            sub_task_count=int(self.sub_task_count or 0),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class SubTaskSchema(TerminusBase):
    task: "TaskSchema"
    name: str
    description: str
    state: str
    sequence: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error: Optional[str]
    touched_node_ids_json: str

    @staticmethod
    def from_pydantic(node: SubTaskNode) -> "SubTaskSchema":
        return SubTaskSchema(
            _id=node.id,
            task=node.task_id,
            name=node.name,
            description=node.description,
            state=node.state,
            sequence=node.sequence,
            started_at=node.started_at,
            finished_at=node.finished_at,
            error=node.error,
            touched_node_ids_json=node.touched_node_ids_json,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def to_pydantic(self) -> SubTaskNode:
        parent = self.task
        return SubTaskNode(
            id=self._id,
            task_id=parent if isinstance(parent, str) else getattr(parent, "_id", ""),
            name=self.name,
            description=self.description,
            state=self.state,
            sequence=int(self.sequence or 0),
            started_at=self.started_at,
            finished_at=self.finished_at,
            error=self.error,
            touched_node_ids_json=self.touched_node_ids_json or "[]",
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
