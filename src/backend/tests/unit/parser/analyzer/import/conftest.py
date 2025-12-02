import pytest
from pathlib import Path
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.services.project_service import ProjectService
from app.core.repository import Repositories
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import ProjectTreeNode
from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager


@pytest.fixture
def project_path() -> Path:
    current_file_path = Path(__file__).resolve()
    current_dir = current_file_path.parent
    return Path(current_dir, "sample_import").absolute()


@pytest.fixture
def setup_project(tmp_path, arangodb_client, project_path):
    """Setup project similar to test_function.py pattern."""
    import shutil

    # Copy the project to a temporary location
    test_project_path = tmp_path / "project"
    print(f"Test project path: {test_project_path}")
    shutil.copytree(project_path, test_project_path)

    db_path = tmp_path / "db" / "sample_import"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    project_node = ProjectNode(
        name="sample_import",
        path=str(test_project_path),
        qname="sample_import",
        description="A test project for imports.",
    )
    scope_manager = ScopeManager(project_node.name, db_path=str(db_path))

    # Create project node in database (matching test_function.py pattern)
    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)
    project_node = project_service.create_node(project_node)

    return project_node, scope_manager, arangodb_client


@pytest.fixture
def project_tree(setup_project) -> ProjectNode:
    project_node, scope_manager, arangodb_client = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node=project_node,
        scope_manager=scope_manager,
        ignore_file_name="v-noc.toml",
        db=arangodb_client,
    )
    orchestrator.resync()

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    projects = project_service.get_all()
    assert len(projects) > 0
    project = projects[0]

    children = project_service.get_children(project.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(**project.model_dump(), children=tree)
    project_tree.children = tree
    return project_tree
