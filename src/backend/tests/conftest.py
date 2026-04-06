import socket
import tempfile
import threading
import time

import httpx
import pytest
import pytest_asyncio

from app.db.client import migrate_base
from app.db.async_terminus_client import AsyncClient
from app.config.settings import get_settings
from app.core.repository import Repositories
from app.db.context import ProjectUoW, RequestDbContext
from app.core.services.project_service import ProjectService

TEST_DB_NAME = "test_db"


@pytest.fixture(scope="session")
def python_lsp_rpc_url():
    """Start the Python language driver (JSON-RPC at POST /rpc) for tests that opt in.

    Same idea as ``jsonrpc_url`` in ``tests/e2e/vn_logger/conftest.py``: bind a
    free port, run uvicorn in a daemon thread, wait until ``initialize`` responds.

    Use only in tests that need the out-of-process driver::

        def test_remote_parse(python_lsp_rpc_url, monkeypatch):
            monkeypatch.setenv("VNOC_LSP_PYTHON_URL", python_lsp_rpc_url)
            ...

    Requires the workspace package ``vnoc-lsp-python`` (``uv sync``).
    """
    pytest.importorskip(
        "vnoc_lsp_python",
        reason="Install workspace package vnoc-lsp-python (uv sync)",
    )
    import uvicorn

    from vnoc_lsp_python.server import build_app

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    _host, port = sock.getsockname()
    sock.close()

    app = build_app()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    url = f"{base}/rpc"

    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "project_path": tempfile.gettempdir(),
            "language": "python",
            "config": {},
        },
        "id": 1,
    }
    deadline = time.time() + 20.0
    while time.time() < deadline:
        try:
            r = httpx.post(url, json=payload, timeout=0.75)
            data = r.json()
            if (
                r.status_code < 500
                and isinstance(data, dict)
                and "result" in data
            ):
                break
        except Exception:
            time.sleep(0.05)
    else:
        server.should_exit = True
        thread.join(timeout=5.0)
        pytest.fail("Python LSP server did not become ready in time")

    try:
        yield url
    finally:
        server.should_exit = True
        thread.join(timeout=10.0)


@pytest.fixture
def monkeypatch_vnoc_lsp_python_url(python_lsp_rpc_url, monkeypatch):
    """Set ``VNOC_LSP_PYTHON_URL`` so :class:`~app.core.parser.drivers.DriverManager` uses the test LSP."""
    monkeypatch.setenv("VNOC_LSP_PYTHON_URL", python_lsp_rpc_url)
    return python_lsp_rpc_url


@pytest_asyncio.fixture(scope="function")
async def terminusdb_client() -> AsyncClient:
    """Provides a connected TerminusDB AsyncClient for tests.

    Creates a fresh test database, yields the connected client, then
    deletes the database and closes the connection on teardown.
    """
    settings = get_settings()
    client = AsyncClient(settings.TERMINUS_HOST)

    # Connect to server (without a specific db) to create the test database
    await client.connect(
        user=settings.TERMINUS_USER,
        key=settings.TERMINUS_KEY,
        team=settings.TERMINUS_TEAM,
    )

    try:
        await client.create_database(
            TEST_DB_NAME,
            team=settings.TERMINUS_TEAM,
            label=TEST_DB_NAME,
            description="Test database for V-NOC",
        )

    except Exception as e:
        # Database may already exist from a previous run
        print(f"database already exists: {e}")

    # Connect to the test database
    await client.set_db(TEST_DB_NAME)
    await migrate_base(client)

    yield client

    # Teardown: disconnect from db, delete it, then close
    try:
        client.db = None
        await client.delete_database(TEST_DB_NAME, team=settings.TERMINUS_TEAM)
    except Exception as e:
        print(
            f"Failed to delete the test database '{TEST_DB_NAME}'. "
            f"It may require manual cleanup. Error: {e}"
        )
    finally:
        await client.close()


@pytest_asyncio.fixture(scope="function")
async def client(terminusdb_client: AsyncClient) -> AsyncClient:
    """Alias for terminusdb_client - used by tests that need the TerminusDB client directly."""
    return terminusdb_client


@pytest_asyncio.fixture(scope="function")
async def arangodb_client(terminusdb_client: AsyncClient) -> AsyncClient:
    """Alias for terminusdb_client - backward compatibility for tests still using old name."""
    return terminusdb_client


@pytest_asyncio.fixture
async def create_repos(terminusdb_client) -> Repositories:
    """Return meta-level Repositories wired to the test database.

    Use for ProjectService and other meta-level operations (create project,
    get project, delete project). For project-scoped operations (files,
    folders, functions, etc.), use project_uow instead.
    """
    return Repositories(terminusdb_client.clone())


@pytest_asyncio.fixture
async def create_project(terminusdb_client):
    ctx = RequestDbContext()
    project_uow = ProjectUoW(terminusdb_client, None, ctx)
    project_service = ProjectService(project_uow)
    project = await project_service.create(
        "Test Project",
        "This is a test project",
        "test_project"
    )
    yield project
    await project_service.delete(project.id)


@pytest_asyncio.fixture
async def project_uow(terminusdb_client, create_project):
    """Return ProjectUoW for project-scoped services.

    Use with services that require ProjectUoW: GroupService, FileService,
    FolderService, ClassService, FunctionService, CallService.
    """

    ctx = RequestDbContext()
    return ProjectUoW(terminusdb_client, create_project, ctx)


@pytest_asyncio.fixture
async def empty_project_uow(terminusdb_client):
    """Return ProjectUoW for project-scoped services.

    Use with services that require ProjectUoW: GroupService, FileService,
    FolderService, ClassService, FunctionService, CallService.
    """

    ctx = RequestDbContext()
    return ProjectUoW(terminusdb_client, None, ctx)
