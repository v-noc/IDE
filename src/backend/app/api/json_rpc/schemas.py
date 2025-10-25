from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LogEventType(str, Enum):
    ENTER = "enter"
    EXIT = "exit"
    ERROR = "error"
    LOG = "log"


class RegisterLogsParams(BaseModel):
    """Params for register_logs JSON-RPC method."""

    chain_id: Optional[str] = Field(
        None, description="Chain ID"
    )
    timestamp: datetime = Field(
        ..., description="Log timestamp (ISO 8601)"
    )
    duration_ms: Optional[float] = Field(
        None, description="Duration in milliseconds"
    )
    event_type: LogEventType = Field(
        ..., description="Event type"
    )
    message: str = Field(
        ..., description="Message"
    )
    level_name: Optional[str] = Field(
        None, description="Log level name (e.g., info, warning, error)"
    )
    payload: Optional[Dict[str, Any]] = Field(
        None, description="Payload for 'enter' events (args/kwargs)"
    )
    result: Optional[Any] = Field(
        None, description="Serialized result for 'exit' events"
    )
    error: Optional[Dict[str, Any]] = Field(
        None, description="Error details for 'error' events"
    )


class RegisterLogsResult(BaseModel):
    """Minimal result placeholder for register_logs."""

    ok: bool = Field(..., description="Operation acknowledgement")
