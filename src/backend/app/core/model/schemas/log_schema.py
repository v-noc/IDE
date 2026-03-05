import json
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
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    FATAL = "FATAL"
    CRITICAL = "CRITICAL"
    NOTSET = "NOTSET"


class LogSchema(DocumentTemplate):
    """
    The schema for the log document.
    """
    event_type: LogEventType
    origin_function: Optional[FunctionSchema]
    timestamp: datetime
    message: str
    level_name: LogLevelName
    duration_ms: Optional[float]
    chain_id: str
    children_logs: Set["LogSchema"]
    payload: Optional[str]  # JSON string to avoid TerminusDB sys:JSON issues
    result: Optional[str]  # JSON string to avoid TerminusDB sys:JSON issues
    error: Optional[str]  # JSON string to avoid TerminusDB sys:JSON issues

    @staticmethod
    def from_pydantic(log: LogNode):
        def _to_json_str(val):
            if val is None:
                return None
            return json.dumps(val) if not isinstance(val, str) else val

        return LogSchema(
            _id=log.id,
            timestamp=log.timestamp,
            event_type=LogEventType(log.event_type),
            message=log.message,
            level_name=LogLevelName(
                log.level_name) if log.level_name else LogLevelName.NOTSET,
            duration_ms=log.duration_ms,
            chain_id=log.chain_id or "",
            children_logs=log.children_logs,
            payload=_to_json_str(log.payload),
            result=_to_json_str(log.result),
            error=_to_json_str(log.error),
            origin_function=log.origin_function,
        )

    def to_pydantic(self):
        def _from_json_str(val):
            if val is None:
                return None
            if isinstance(val, str) and val.strip().startswith(("{", "[")):
                return json.loads(val)
            return val

        return LogNode(
            id=self._id,
            timestamp=self.timestamp,
            event_type=self.event_type.value if hasattr(
                self.event_type, "value") else str(self.event_type),
            message=self.message,
            level_name=None if self.level_name is LogLevelName.NOTSET else (
                self.level_name.value if hasattr(self.level_name, "value") else str(self.level_name)),
            duration_ms=self.duration_ms,
            chain_id=self.chain_id or None,
            children_logs=self.children_logs,
            payload=_from_json_str(self.payload),
            result=_from_json_str(self.result),
            error=_from_json_str(self.error),
            origin_function=self.origin_function,
        )
