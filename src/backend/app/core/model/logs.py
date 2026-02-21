from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Literal, Set

from pydantic import Field, BaseModel


class LogEventType(str, Enum):
    ENTER = "enter"
    EXIT = "exit"
    ERROR = "error"
    LOG = "log"


class LogLevelName(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"
    TRACE = "trace"
    FATAL = "fatal"
    CRITICAL = "critical"
    NOTSET = "notset"


class LogNode(BaseModel):
    id: str = Field(
        ..., description="Log ID"
    )
    timestamp: datetime = Field(
        ..., description="Event timestamp (UTC ISO 8601)"
    )
    event_type: Literal["enter", "exit", "error", "log"] = Field(
        ..., description="Event type"
    )
    message: str = Field(
        ..., description="Event message"
    )
    level_name: Optional[LogLevelName] = Field(
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
    origin_function: str = Field(
        ..., description="Origin function"
    )
    children_logs: Set[str] = Field(
        default_factory=set, description="Children logs"
    )

    @staticmethod
    def from_raw_dict(raw_dict):
        return LogNode(
            id=raw_dict["@id"],
            timestamp=raw_dict.get("timestamp"),
            event_type=LogEventType(raw_dict.get("event_type")),
            message=raw_dict.get("message"),
            level_name=LogLevelName(raw_dict.get("level_name")),
            duration_ms=raw_dict.get("duration_ms"),
            chain_id=raw_dict.get("chain_id"),
            payload=raw_dict.get("payload"),
            result=raw_dict.get("result"),
            error=raw_dict.get("error"),
            origin_function=raw_dict.get("origin_function"),
            children_logs=raw_dict.get("children_logs", set()),
        )

    def to_raw_dict(self):
        return {
            "@id": self.id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "message": self.message,
            "level_name": self.level_name,
            "duration_ms": self.duration_ms,
            "chain_id": self.chain_id,
            "payload": self.payload,
            "result": self.result,
            "error": self.error,
            "origin_function": self.origin_function,
            "children_logs": set(self.children_logs),
        }
