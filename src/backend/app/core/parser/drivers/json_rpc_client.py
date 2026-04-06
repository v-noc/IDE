"""JSON-RPC 2.0 HTTP client for a remote language driver (Python or ts_js)."""

from __future__ import annotations

import itertools
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.parser.ast.models import BaseNode
from app.core.parser.drivers.protocol import (
    CallFrameResult,
    FileIdResult,
    FolderIdResult,
    InitializeResult,
    ParseResult,
    parse_symbol_list,
)
from app.core.parser.jedi_adapter.call_resolver.call_resolver import (
    CallFrameStack,
)

logger = logging.getLogger(__name__)


class DriverRpcError(RuntimeError):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data


class JsonRpcLanguageDriver:
    """
    Implements LanguageDriver over HTTP POST {url} with JSON-RPC 2.0 payloads.
    """

    def __init__(
        self,
        rpc_url: str,
        *,
        language: str = "python",
        timeout: float = 120.0,
    ):
        self._url = rpc_url.rstrip("/")
        if not self._url.endswith("/rpc"):
            self._url = f"{self._url}/rpc"
        self._language = language
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._id_counter = itertools.count(1)

    async def _client_(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _call(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        client = await self._client_()
        req_id = next(self._id_counter)
        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "id": req_id,
        }
        if params is not None:
            payload["params"] = params
        if self._language == "typescript":
            extra = ""
            if params:
                fp = params.get("file_path")
                if isinstance(fp, str):
                    extra += f" file={fp}"
                if method == "resolve_calls":
                    calls = params.get("calls")
                    if isinstance(calls, list):
                        extra += f" calls={len(calls)}"
                if method == "parse_file":
                    c = params.get("content")
                    if isinstance(c, str):
                        extra += f" bytes={len(c.encode('utf-8'))}"
            logger.info(
                "ts_js RPC -> %s id=%s%s", method, req_id, extra
            )
        try:
            r = await client.post(self._url, json=payload)
        except httpx.HTTPError as e:
            logger.error(
                "RPC HTTP failure url=%s method=%s id=%s: %s",
                self._url,
                method,
                req_id,
                e,
            )
            raise
        body = r.json()
        if body.get("error"):
            err = body["error"]
            raise DriverRpcError(
                err.get("code", -32603),
                err.get("message", "RPC error"),
                err.get("data"),
            )
        return body.get("result")

    async def initialize(
        self, project_path: str, config: Optional[dict] = None
    ) -> InitializeResult:
        raw = await self._call(
            "initialize",
            {
                "project_path": project_path,
                "language": self._language,
                "config": config or {},
            },
        )
        return InitializeResult.model_validate(raw)

    async def parse_file(
        self, file_path: str, content: str, *, resolve_mro: bool = False
    ) -> ParseResult:
        raw = await self._call(
            "parse_file",
            {
                "file_path": file_path,
                "content": content,
                "resolve_mro": resolve_mro,
            },
        )
        nodes = parse_symbol_list(raw["nodes"])
        return ParseResult(
            nodes=nodes,
            content=raw["content"],
            modified=raw.get("modified", False),
        )

    async def resolve_calls(
        self, file_path: str, calls: List[BaseNode]
    ) -> CallFrameResult:
        call_payloads = [c.model_dump(mode="json") for c in calls]
        raw = await self._call(
            "resolve_calls",
            {"file_path": file_path, "calls": call_payloads},
        )
        stack = CallFrameStack.model_validate(raw["call_frame_stack"])
        return CallFrameResult(call_frame_stack=stack)

    async def read_or_inject_file_id(self, file_path: str) -> FileIdResult:
        raw = await self._call(
            "read_or_inject_file_id", {"file_path": file_path}
        )
        return FileIdResult.model_validate(raw)

    async def read_or_inject_folder_id(
        self, folder_path: str
    ) -> FolderIdResult:
        raw = await self._call(
            "read_or_inject_folder_id", {"folder_path": folder_path}
        )
        return FolderIdResult.model_validate(raw)

    async def shutdown(self) -> None:
        try:
            await self._call("shutdown", {})
        except Exception:
            logger.exception("shutdown RPC failed")
        await self.aclose()

    async def is_alive(self) -> bool:
        if self._client is None or self._client.is_closed:
            return False
        return True
