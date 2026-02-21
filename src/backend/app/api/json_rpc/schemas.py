from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.core.model.logs import LogLevelName, LogEventType


class RegisterLogsParams(BaseModel):
    """Params for register_logs JSON-RPC method."""

    chain_id: Optional[str] = Field(
        None, description="Chain ID"
    )
    id: Optional[str] = Field(
        None, description="Log ID"
    )
    parent_log_id: Optional[str] = Field(
        None, description="Parent log ID"
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
    level_name: Optional[LogLevelName] = Field(
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
    function_id: Optional[str] = Field(
        None, description="Parent function ID"
    )


class RegisterLogsBatchParams(BaseModel):
    """Batch endpoint params - list of individual logs."""
    logs: List[RegisterLogsParams]


class RegisterLogsResult(BaseModel):
    """Minimal result placeholder for register_logs."""

    ok: bool = Field(..., description="Operation acknowledgement")


class RegisterLogsBatchResult(BaseModel):
    ok: bool
    total: int
    succeeded: int
    failed: int
    errors: Optional[List[dict]] = None  #
