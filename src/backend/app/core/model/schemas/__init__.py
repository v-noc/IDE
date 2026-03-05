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
    CallSchema
)
from .log_schema import LogSchema, LogLevelName, LogEventType
from .metadata import CodePositionSchema, ThemeConfigSchema, DocumentSchema
from .structure_schema import StructureGroupSchema, FileSchema, FolderSchema, ProjectSchema

__all__ = [
    "BaseSchema",
    "TerminusBase",
    "CallGroupSchema",
    "CodeElementGroupSchema",
    "ClassSchema",
    "FunctionSchema",
    "CallSchema",
    "LogSchema",
    "LogLevelName",
    "LogEventType",
    "CodePositionSchema",
    "ThemeConfigSchema",
    "DocumentSchema",
    "StructureGroupSchema",
    "FileSchema",
    "FolderSchema",
    "ProjectSchema"
]


async def ensure_schema(client: AsyncClient, title: str, description: str, authors: list[str]):
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
    schema_obj.add_obj(StructureGroupSchema.__name__, StructureGroupSchema)

    # code element schema
    schema_obj.add_obj(CodeElementGroupSchema.__name__, CodeElementGroupSchema)
    schema_obj.add_obj(ClassSchema.__name__, ClassSchema)
    schema_obj.add_obj(FunctionSchema.__name__, FunctionSchema)
    schema_obj.add_obj(CallGroupSchema.__name__, CallGroupSchema)
    schema_obj.add_obj(CallSchema.__name__, CallSchema)

    await schema_obj.commit(client, f"Initialize schema for {title}", full_replace=True)
