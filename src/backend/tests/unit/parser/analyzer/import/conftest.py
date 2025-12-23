import pytest
import pytest_asyncio
import shutil
from pathlib import Path
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.services.project_service import ProjectService
from app.core.repository import Repositories
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import ProjectTreeNode
from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager


FIXTURE_PROJECT = Path(__file__).parent / "sample_import"
PROJECT_NAME = "sample_import"


@pytest.fixture
def project_path() -> Path:
    current_file_path = Path(__file__).resolve()
    current_dir = current_file_path.parent
    return Path(current_dir, "sample_import").absolute()


@pytest_asyncio.fixture
async def setup_project(tmp_path, arangodb_client, project_path):
    project_path = tmp_path / "sample_import"
    shutil.copytree(FIXTURE_PROJECT, project_path)

    db_path = tmp_path / "db" / PROJECT_NAME
    db_path.parent.mkdir(parents=True, exist_ok=True)

    project_node = ProjectNode(
        name=PROJECT_NAME,
        path=str(project_path),
        qname=PROJECT_NAME,
        description="Test Project",
    )
    scope_manager = ScopeManager(PROJECT_NAME, db_path=str(db_path))
    await scope_manager.initialize()

    # Create project node in database (matching test_function.py pattern)
    repos = Repositories(arangodb_client)
    await repos.ensure_collections()
    project_service = ProjectService(repos)
    project_node = await project_service.create_node(project_node)

    return project_node, scope_manager, arangodb_client


@pytest_asyncio.fixture
async def project_tree(setup_project) -> ProjectNode:
    project_node, scope_manager, arangodb_client = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node=project_node,
        scope_manager=scope_manager,
        ignore_file_name="v-noc.toml",
        db=arangodb_client,
    )
    await orchestrator.resync()

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    projects = await project_service.get_all()
    assert len(projects) > 0
    project = projects[0]

    children = await project_service.get_children(project.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(**project.model_dump(), children=tree)
    project_tree.children = tree
    return project_tree
