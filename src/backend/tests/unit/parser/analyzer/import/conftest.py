import pytest
from pathlib import Path
from app.core.parser.graph_builder import GraphBuilder
from app.core.services.project_service import ProjectService
from app.core.repository import Repositories
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import ProjectTreeNode
from app.core.schemas.tree import ProjectNode


@pytest.fixture
def project_path() -> Path:
    current_file_path = Path(__file__).resolve()
    current_dir = current_file_path.parent
    return Path(current_dir, "sample_import").absolute()


@pytest.fixture
def project_tree(arangodb_client, project_path) -> ProjectNode:
    graph_builder = GraphBuilder(
        project_path=project_path.as_posix(), ignore_file_name="v-noc.toml", db=arangodb_client
    )
    graph_builder.build("sample_import", "A test project for imports.")

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
