"""HTTP server: JSON-RPC at POST /rpc, prints READY port=<n> for process managers."""

from __future__ import annotations

import argparse
import logging
import socket

import uvicorn
import fastapi_jsonrpc as jsonrpc

from vnoc_lsp_python.rpc import build_entrypoint
from vnoc_lsp_python.service import PythonDriverService

logger = logging.getLogger(__name__)


def _pick_port(preferred: int) -> int:
    if preferred != 0:
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def build_app():
    service = PythonDriverService()
    api = jsonrpc.API()
    entry = build_entrypoint(service)
    api.bind_entrypoint(entry)
    return api


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser(
        description="v-noc Python language driver (JSON-RPC)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=9002, help="0 = auto free port")
    args = p.parse_args(argv)

    port = _pick_port(args.port)
    print(f"READY port={port}", flush=True)

    app = build_app()
    uvicorn.run(app, host=args.host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
