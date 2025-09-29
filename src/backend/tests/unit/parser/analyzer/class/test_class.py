from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import AnyTreeNode

from pathlib import Path
from typing import List


current_file_path = Path(__file__).resolve()
print("Current file path:", current_file_path)

# Get the directory of the current file
current_dir = current_file_path.parent
PROJECT_PATH = Path(current_dir, "./sample_class").absolute()


def test_class_analysis(arangodb_client):
    graph_builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        ignore_file_name=None,
        db=arangodb_client
    )
    graph_builder.build(
        "Protector", "Protector is a tool for protecting your code.")

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    project = project_service.get_all()

    children = project_service.get_children(project[0].id)
    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()
    print(tree)
