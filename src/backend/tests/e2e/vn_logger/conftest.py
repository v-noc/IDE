import pytest
import pytest_asyncio
from pathlib import Path
import threading
import time
import socket
import requests
import shutil
from app.db.async_terminus_client import AsyncClient
from app.db.client import get_terminus_client, migrate_base
from app.db.context import RequestDbContext, ProjectUoW
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.services.project_service import ProjectService
from app.api.json_rpc.app import app as jsonrpc_app
from app.config.settings import get_settings
import uvicorn

from tests.conftest import TEST_DB_NAME

current_file_path = Path(__file__).resolve()
current_dir = current_file_path.parent
PROJECT_PATH = Path(current_dir, "./sample_project").absolute()

# Client created in the uvicorn server's event loop (cleared on fixture teardown)
_server_terminus_client: AsyncClient | None = None


@pytest_asyncio.fixture()
async def create_sample_project(terminusdb_client: AsyncClient, tmp_path):
    project_path = tmp_path / "sample_project"
    shutil.copytree(PROJECT_PATH, project_path)

    ctx = RequestDbContext()
    uow = ProjectUoW(terminusdb_client, None, ctx)
    project_service = ProjectService(uow)
    project_node = await project_service.create(
        "Protector",
        "Protector is a tool for protecting your code.",
        project_path.as_posix(),
    )

    uow_with_project = ProjectUoW(terminusdb_client, project_node, ctx)
    orchestrator = GraphBuilderOrchestrator(
        project_node=project_node,
        uow=uow_with_project,
        ignore_file_name=None,
    )
    await orchestrator.resync()
    return project_node


async def _create_server_terminus_client() -> AsyncClient:
    """Create a TerminusDB client in the server's event loop (avoids event loop mismatch)."""
    global _server_terminus_client
    if _server_terminus_client is None:
        settings = get_settings()
        client = AsyncClient(settings.TERMINUS_HOST)
        await client.connect(
            user=settings.TERMINUS_USER,
            key=settings.TERMINUS_KEY,
            team=settings.TERMINUS_TEAM,
        )
        await client.set_db(TEST_DB_NAME)
        await migrate_base(client)
        _server_terminus_client = client
    return _server_terminus_client


@pytest.fixture()
def jsonrpc_url(terminusdb_client: AsyncClient) -> str:
    """Start a real uvicorn server for JSON-RPC and return its URL.

    The terminusdb_client fixture is used only to ensure the test DB exists.
    The server creates its own client in its event loop to avoid 'bound to
    different event loop' errors.
    """
    global _server_terminus_client
    _server_terminus_client = None

    jsonrpc_app.dependency_overrides[get_terminus_client] = _create_server_terminus_client

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
        _server_terminus_client = None
