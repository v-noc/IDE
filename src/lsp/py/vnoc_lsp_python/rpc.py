"""JSON-RPC entrypoint (fastapi-jsonrpc) for the Python driver."""

from __future__ import annotations

from typing import Any, Dict, List

import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from vnoc_lsp_python.service import PythonDriverService


class InitializeParams(BaseModel):
    project_path: str
    language: str = "python"
    config: Dict[str, Any] = Field(default_factory=dict)


class ParseFileParams(BaseModel):
    file_path: str
    content: str
    resolve_mro: bool = False


class ResolveCallsParams(BaseModel):
    file_path: str
    calls: List[Dict[str, Any]]


class ReadFileParams(BaseModel):
    file_path: str


class ReadFolderParams(BaseModel):
    folder_path: str


class ShutdownParams(BaseModel):
    """JSON-RPC ``shutdown`` may send ``params: {}``."""

    model_config = ConfigDict(extra="ignore")


def build_entrypoint(service: PythonDriverService) -> jsonrpc.Entrypoint:
    entry = jsonrpc.Entrypoint("/rpc")

    @entry.method()
    async def initialize(params: InitializeParams = jsonrpc.Params(...)) -> dict:
        return await run_in_threadpool(
            service.initialize, params.project_path, params.language
        )

    @entry.method()
    async def parse_file(params: ParseFileParams = jsonrpc.Params(...)) -> dict:
        return await run_in_threadpool(
            service.parse_file,
            params.file_path,
            params.content,
            params.resolve_mro,
        )

    @entry.method()
    async def resolve_calls(params: ResolveCallsParams = jsonrpc.Params(...)) -> dict:
        return await run_in_threadpool(
            service.resolve_calls, params.file_path, params.calls
        )

    @entry.method()
    async def read_or_inject_file_id(
        params: ReadFileParams = jsonrpc.Params(...),
    ) -> dict:
        return await run_in_threadpool(
            service.read_or_inject_file_id, params.file_path
        )

    @entry.method()
    async def read_or_inject_folder_id(
        params: ReadFolderParams = jsonrpc.Params(...),
    ) -> dict:
        return await run_in_threadpool(
            service.read_or_inject_folder_id, params.folder_path
        )

    @entry.method()
    async def shutdown(
        params: ShutdownParams = jsonrpc.Params(ShutdownParams()),
    ) -> dict:
        return {"status": "ok"}

    return entry
