"""
Language driver contract: shared result types and the async interface used by
graph_builder and the JSON-RPC client.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from app.core.parser.ast.models import BaseNode
from app.core.parser.jedi_adapter.call_resolver.call_resolver import CallFrameStack


class InitializeParams(BaseModel):
    project_path: str
    language: str = "python"
    config: Dict[str, Any] = Field(default_factory=dict)


class InitializeResult(BaseModel):
    status: str = "ok"
    extensions: List[str] = Field(default_factory=list)


class ParseFileParams(BaseModel):
    file_path: str
    content: str
    resolve_mro: bool = False


class ParseResult(BaseModel):
    nodes: List[BaseNode]
    content: str
    modified: bool


class ResolveCallsParams(BaseModel):
    file_path: str
    calls: List[BaseNode]


class CallFrameResult(BaseModel):
    call_frame_stack: CallFrameStack


class ReadOrInjectFileParams(BaseModel):
    file_path: str


class FileIdResult(BaseModel):
    file_id: str
    modified: bool


class ReadOrInjectFolderParams(BaseModel):
    folder_path: str


class FolderIdResult(BaseModel):
    folder_id: str
    modified: bool


class ShutdownResult(BaseModel):
    status: str = "ok"


@runtime_checkable
class LanguageDriver(Protocol):
    async def initialize(
        self, project_path: str, config: Optional[Dict[str, Any]] = None
    ) -> InitializeResult: ...

    async def parse_file(
        self, file_path: str, content: str, *, resolve_mro: bool = False
    ) -> ParseResult: ...

    async def resolve_calls(
        self, file_path: str, calls: List[BaseNode]
    ) -> CallFrameResult: ...

    async def read_or_inject_file_id(self, file_path: str) -> FileIdResult: ...

    async def read_or_inject_folder_id(self, folder_path: str) -> FolderIdResult: ...

    async def shutdown(self) -> None: ...

    async def is_alive(self) -> bool: ...


def parse_symbol_dict(data: Dict[str, Any]) -> BaseNode:
    """Deserialize one wire-format symbol (recursive children)."""
    from app.core.parser.ast.models import CallNode, ClassNode, FunctionNode

    children_raw = data.get("children") or []
    children = [parse_symbol_dict(c) for c in children_raw]
    payload = {**data, "children": children}
    t = payload.get("type")
    if t == "call":
        return CallNode.model_validate(payload)
    if t == "function":
        return FunctionNode.model_validate(payload)
    if t == "class":
        return ClassNode.model_validate(payload)
    raise ValueError(f"Unknown symbol type: {t}")


def parse_symbol_list(nodes: List[Dict[str, Any]]) -> List[BaseNode]:
    return [parse_symbol_dict(n) for n in nodes]
