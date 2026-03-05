from datetime import datetime
from typing import Set, Optional

from app.core.model.logs import LogNode
from app.db.schema.schema import DocumentTemplate
from app.db.woqlschema import EnumTemplate
from .code_element_schema import FunctionSchema


class LogEventType(EnumTemplate):
    ENTER = "enter"
    EXIT = "exit"
    ERROR = "error"
    LOG = "log"


class LogLevelName(EnumTemplate):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"
    TRACE = "trace"
    FATAL = "fatal"
    CRITICAL = "critical"
    NOTSET = "notset"


class LogSchema(DocumentTemplate):
    """
    The schema for the log document.
    """
    event_type: LogEventType
    origin_function: FunctionSchema
    timestamp: datetime
    message: str
    level_name: LogLevelName
    duration_ms: Optional[float]
    chain_id: str
    children_logs: Set["LogSchema"]
    payload: Optional[dict]
    result: Optional[dict]
    error: Optional[dict]

    @staticmethod
    def from_pydantic(log: LogNode):
        return LogSchema(
            _id=log.id,
            timestamp=log.timestamp,
            event_type=LogEventType(log.event_type),
            message=log.message,
            level_name=LogLevelName(
                log.level_name) if log.level_name else LogLevelName.NOTSET,
            duration_ms=log.duration_ms,
            chain_id=log.chain_id,
            children_logs=log.children_logs,
            payload=log.payload,
            result=log.result,
            error=log.error,
            origin_function=log.origin_function,
        )

    def to_pydantic(self):
        return LogNode(
            id=self._id,
            timestamp=self.timestamp,
            event_type=self.event_type.value if hasattr(
                self.event_type, "value") else str(self.event_type),
            message=self.message,
            level_name=None if self.level_name is LogLevelName.NOTSET else (
                self.level_name.value if hasattr(self.level_name, "value") else str(self.level_name)),
            duration_ms=self.duration_ms,
            chain_id=self.chain_id,
            children_logs=self.children_logs,
            payload=self.payload,
            result=self.result,
            error=self.error,
            origin_function=self.origin_function,
        )
