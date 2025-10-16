import pytest
from pathlib import Path
import threading
import time
import socket
import requests
from arango.database import StandardDatabase
from app.core.parser.graph_builder import GraphBuilder
from app.api.json_rpc.app import app as jsonrpc_app
from app.db.client import get_db
import uvicorn

current_file_path = Path(__file__).resolve()
print("Current file path:", current_file_path)
current_dir = current_file_path.parent
PROJECT_PATH = Path(current_dir, "./sample_project").absolute()


@pytest.fixture()
def create_sample_project(arangodb_client):
    builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        ignore_file_name=None,
        db=arangodb_client
    )
    builder.build(
        "Protector", "Protector is a tool for protecting your code.")


@pytest.fixture()
def jsonrpc_url(arangodb_client: StandardDatabase) -> str:
    """Start a real uvicorn server for JSON-RPC and return its URL."""

    def override_get_db():
        return arangodb_client

    jsonrpc_app.dependency_overrides[get_db] = override_get_db

    # Pick a free port
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()

    config = uvicorn.Config(
        jsonrpc_app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    url = f"{base_url}/api/v1/jsonrpc"

    # Wait until server starts accepting requests
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            # Expect JSON-RPC error or 200/4xx; reaching transport is enough
            requests.post(
                url,
                json={"jsonrpc": "2.0", "method": "__ping__", "id": 1},
                timeout=0.5,
            )
            break
        except Exception:
            time.sleep(0.05)

    try:
        yield url
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        jsonrpc_app.dependency_overrides.clear()
