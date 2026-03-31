"""JSON-RPC entrypoint (fastapi-jsonrpc) for the Python driver."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import fastapi_jsonrpc as jsonrpc
from fastapi import Body
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from vnoc_lsp_python.service import PythonDriverService

logger = logging.getLogger(__name__)


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


def build_entrypoint(service: PythonDriverService) -> jsonrpc.Entrypoint:
    entry = jsonrpc.Entrypoint("/rpc")

    @entry.method()
    async def initialize(params: InitializeParams = Body(...)) -> dict:
        return await run_in_threadpool(
            service.initialize, params.project_path, params.language
        )

    @entry.method()
    async def parse_file(params: ParseFileParams = Body(...)) -> dict:
        return await run_in_threadpool(
            service.parse_file,
            params.file_path,
            params.content,
            params.resolve_mro,
        )

    @entry.method()
    async def resolve_calls(params: ResolveCallsParams = Body(...)) -> dict:
        return await run_in_threadpool(
            service.resolve_calls, params.file_path, params.calls
        )

    @entry.method()
    async def read_or_inject_file_id(params: ReadFileParams = Body(...)) -> dict:
        return await run_in_threadpool(
            service.read_or_inject_file_id, params.file_path
        )

    @entry.method()
    async def read_or_inject_folder_id(params: ReadFolderParams = Body(...)) -> dict:
        return await run_in_threadpool(
            service.read_or_inject_folder_id, params.folder_path
        )

    @entry.method()
    async def shutdown(params: Optional[dict] = Body(None)) -> dict:
        return {"status": "ok"}

    return entry
