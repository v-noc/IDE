from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.model.conversation_nodes import TaskNode


class SubTaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubTask(BaseModel):
    """One persisted workflow step under a task."""

    id: str = ""
    name: str
    description: str = ""
    state: SubTaskState = SubTaskState.PENDING
    sequence: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    touched_node_ids: list[str] = Field(default_factory=list)


class Task(BaseModel):
    """Standalone task document (not the inline TaskPart in a message)."""

    id: str = ""
    name: str = ""
    description: str = ""
    conversation_id: str = ""
    message_id: str = ""
    state: TaskState = TaskState.PENDING
    progress: float = 0.0
    progress_message: str = ""
    workflow_name: Optional[str] = None
    workflow_params: Optional[dict[str, Any]] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    sub_task_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_task_node(self, task_id: str) -> TaskNode:
        return TaskNode(
            id=task_id,
            name=self.name or "Task",
            description=self.description,
            conversation_id=self.conversation_id,
            message_id=self.message_id,
            state=self.state.value,
            progress=self.progress,
            progress_message=self.progress_message,
            workflow_name=self.workflow_name,
            workflow_params_json=json.dumps(self.workflow_params)
            if self.workflow_params is not None
            else None,
            started_at=self.started_at,
            finished_at=self.finished_at,
            error=self.error,
            result_json=json.dumps(self.result) if self.result is not None else None,
            sub_task_count=self.sub_task_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_task_node(node: TaskNode) -> "Task":
        params: Optional[dict[str, Any]] = None
        if node.workflow_params_json:
            try:
                params = json.loads(node.workflow_params_json)
            except json.JSONDecodeError:
                params = None
        result: Any = None
        if node.result_json:
            try:
                result = json.loads(node.result_json)
            except json.JSONDecodeError:
                result = node.result_json
        return Task(
            id=node.id,
            name=node.name,
            description=node.description,
            conversation_id=node.conversation_id,
            message_id=node.message_id,
            state=TaskState(node.state),
            progress=node.progress,
            progress_message=node.progress_message,
            workflow_name=node.workflow_name,
            workflow_params=params,
            started_at=node.started_at,
            finished_at=node.finished_at,
            error=node.error,
            result=result,
            sub_task_count=node.sub_task_count,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )
