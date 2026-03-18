from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(BaseModel):
    id: str
    name: str
    state: TaskState
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress: float = 0.0          # 0.0 → 1.0
    progress_message: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
