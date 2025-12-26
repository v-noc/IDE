import pytest_asyncio
import shutil
from pathlib import Path

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.discovery.change_detector import ChangeDetector
from app.core.parser.graph_builder.discovery.scanner import FileScanner
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.repository import Repositories

# Locate the existing sample project fixture relative to this test directory
FIXTURE_PROJECT = Path(__file__).parent.parent / "simple_project"
PROJECT_NAME = "sample_project"


@pytest_asyncio.fixture
async def hierarchy_setup(tmp_path, create_repos: Repositories):
    """
    Sets up a temporary project environment with initialized components.
    Does NOT run the initial sync.
    """
    # Setup paths
    project_path = tmp_path / "project"

    if FIXTURE_PROJECT.exists():
        shutil.copytree(FIXTURE_PROJECT, project_path)
    else:
        # Fallback for robustness if fixture moves
        project_path.mkdir()
        (project_path / "main.py").write_text("# main")
        (project_path / "v-noc.toml").write_text("")

    # Initialize components
    project_node = ProjectNode(
        name=PROJECT_NAME,
        path=str(project_path),
        qname=PROJECT_NAME,
        description="Test Project",
    )

    repos = create_repos

    await repos.ensure_collections()

    # Ensure clean DB state for the project
    # (Optional but good practice if DB is shared/dirty)

    jedi_manager = JediProjectManager(project_path)
    collector = Collector(project_node, repos, jedi_manager)

    change_detector = ChangeDetector(repos)
    scanner = FileScanner(str(project_path), ignore_file_name="v-noc.toml")

    context = {
        "project_path": project_path,
        "repos": repos,
        "collector": collector,
        "change_detector": change_detector,
        "scanner": scanner,
        "project_node": project_node,
        "project_name": PROJECT_NAME
    }

    yield context


@pytest_asyncio.fixture
async def synced_project(hierarchy_setup):
    """
    Returns the context after an initial sync has been performed.
    This ensures the DB is populated with the initial state.
    """
    ctx = hierarchy_setup

    # Run initial sync
    scan_result = ctx["scanner"].scan()
    change_set = await ctx["change_detector"].detect_changes(scan_result)

    # We expect some changes initially
    # assert change_set.has_changes() or change_set.has_folder_changes()

    await ctx["collector"].sync_structure(change_set, scan_result)

    return ctx
