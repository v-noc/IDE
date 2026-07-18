import enum
from app.db.async_terminus_client import AsyncClient
from app.db.woqlschema import *
from app.db.schema import schema
from app.db import woqlschema
from .base import BaseSchema, TerminusBase
from .code_element_schema import (
    CallGroupSchema,
    CodeElementGroupSchema,
    ClassSchema,
    FunctionSchema,
    CallSchema,
    PlayGroundSchema,
)
from .log_schema import LogSchema, LogLevelName, LogEventType
from .metadata import CodePositionSchema, ThemeConfigSchema, DocumentSchema
from .structure_schema import (
    StructureGroupSchema,
    FileSchema,
    FolderSchema,
    ProjectSchema,
    CodeContentSchema,
)
from .test_schema import TestConfigSchema, TestCaseSchema, TestLinkSchema
from .conversation_schema import ConversationSchema
from .task_schema import BoardSchema, TaskSchema

__all__ = [
    "BaseSchema",
    "TerminusBase",
    "CallGroupSchema",
    "CodeElementGroupSchema",
    "ClassSchema",
    "FunctionSchema",
    "CallSchema",
    "PlayGroundSchema",
    "LogSchema",
    "LogLevelName",
    "LogEventType",
    "CodePositionSchema",
    "ThemeConfigSchema",
    "DocumentSchema",
    "StructureGroupSchema",
    "FileSchema",
    "FolderSchema",
    "ProjectSchema",
    "CodeContentSchema",
    "TestConfigSchema",
    "TestCaseSchema",
    "TestLinkSchema",
    "ConversationSchema",
    "TaskSchema",
    "BoardSchema",
]


async def ensure_schema(
    client: AsyncClient,
    title: str,
    description: str,
    authors: list[str],
):
    schema_obj = WOQLSchema(
        title=title,
        description=description,
        authors=authors,
    )
    schema_obj.add_obj(TerminusBase.__name__, TerminusBase)
    schema_obj.add_obj(BaseSchema.__name__, BaseSchema)

    # log schema
    schema_obj.add_obj(LogSchema.__name__, LogSchema)
    schema_obj.add_obj(LogLevelName.__name__, LogLevelName)
    schema_obj.add_obj(LogEventType.__name__, LogEventType)
    schema_obj.add_obj(DocumentSchema.__name__, DocumentSchema)
    schema_obj.add_obj(ThemeConfigSchema.__name__, ThemeConfigSchema)
    schema_obj.add_obj(CodePositionSchema.__name__, CodePositionSchema)

    # structure schema
    schema_obj.add_obj(FolderSchema.__name__, FolderSchema)
    schema_obj.add_obj(FileSchema.__name__, FileSchema)
    schema_obj.add_obj(CodeContentSchema.__name__, CodeContentSchema)
    schema_obj.add_obj(StructureGroupSchema.__name__, StructureGroupSchema)

    # code element schema
    schema_obj.add_obj(CodeElementGroupSchema.__name__, CodeElementGroupSchema)
    schema_obj.add_obj(ClassSchema.__name__, ClassSchema)
    schema_obj.add_obj(FunctionSchema.__name__, FunctionSchema)
    schema_obj.add_obj(CallGroupSchema.__name__, CallGroupSchema)
    schema_obj.add_obj(CallSchema.__name__, CallSchema)
    schema_obj.add_obj(PlayGroundSchema.__name__, PlayGroundSchema)
    schema_obj.add_obj(TestConfigSchema.__name__, TestConfigSchema)
    schema_obj.add_obj(TestCaseSchema.__name__, TestCaseSchema)
    schema_obj.add_obj(TestLinkSchema.__name__, TestLinkSchema)

    # agent conversation schema
    schema_obj.add_obj(ConversationSchema.__name__, ConversationSchema)

    # task management schema
    schema_obj.add_obj(TaskSchema.__name__, TaskSchema)
    schema_obj.add_obj(BoardSchema.__name__, BoardSchema)

    await schema_obj.commit(
        client,
        f"Initialize schema for {title}",
        full_replace=False,
    )


_conversation_schema_ready: set[str] = set()


async def ensure_conversation_schema(client: AsyncClient) -> None:
    """Register ConversationSchema on project DBs created before agent v2."""
    db = getattr(client, "db", None) or ""
    if db in _conversation_schema_ready:
        return

    # Partial class-only commits fail (datetime → schema#datetime witness).
    # Re-run the full schema ensure — idempotent with full_replace=False.
    await ensure_schema(
        client,
        title="V-NOC Schema",
        description="V-NOC code analysis graph schema",
        authors=["V-NOC Team"],
    )
    _conversation_schema_ready.add(db)


_task_schema_ready: set[str] = set()


async def ensure_task_schema(client: AsyncClient) -> None:
    """Register task schemas on project DBs created before task management."""
    db = getattr(client, "db", None) or ""
    if db in _task_schema_ready:
        return
    await ensure_schema(
        client,
        title="V-NOC Schema",
        description="V-NOC code analysis graph schema",
        authors=["V-NOC Team"],
    )
    _task_schema_ready.add(db)
