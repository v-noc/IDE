from datetime import datetime
from typing import Any, Dict, Optional, Literal

from pydantic import Field, BaseModel


class LogNode(BaseModel):
    timestamp: datetime = Field(
        ..., description="Event timestamp (UTC ISO 8601)"
    )
    event_type: Literal["enter", "exit", "error", "log"] = Field(
        ..., description="Event type"
    )
    message: str = Field(
        ..., description="Event message"
    )
    level_name: Optional[str] = Field(
        default=None, description="Log level name (info, warning, error)"
    )
    duration_ms: Optional[float] = Field(
        default=None, description="Duration in milliseconds (for exit events)"
    )
    chain_id: Optional[str] = Field(
        default=None,
        description="Correlation/chain identifier for grouped logs",
    )
    payload: Optional[Dict[str, Any]] = Field(
        default=None, description="Payload for 'enter' events (args/kwargs)"
    )
    result: Optional[Any] = Field(
        default=None, description="Serialized result for 'exit' events"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None, description="Error details for 'error' events"
    )
