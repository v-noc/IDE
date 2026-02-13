from datetime import datetime
from .base import TerminusBase
from app.db.woqlschema import EnumTemplate


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


class LogSchema(TerminusBase):
    """
    The schema for the log document.
    """
    event_type: LogEventType
    timestamp: datetime
    message: str
    level_name: LogLevelName
    duration_ms: float
    chain_id: str
    payload: dict
    result: dict
    error: dict
