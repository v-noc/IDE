from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder

from pathlib import Path


current_file_path = Path(__file__).resolve()
print("Current file path:", current_file_path)

# Get the directory of the current file
current_dir = current_file_path.parent
PROJECT_PATH = Path(current_dir, "./simple_project").absolute()


def test_graph_builder(arangodb_client):
    graph_builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        ignore_file_name="./v-noc.toml",
        db=arangodb_client
    )
    graph_builder.build(
        "Protector", "Protector is a tool for protecting your code.")

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    project = project_service.get_all()
    print(project)

    ff = project_service.get_children(project[0].id)

    tree_builder = TreeBuilder(ff)
    tree = tree_builder.build()

    # The root should have 3 children: main.py, app/, and core/
    assert len(tree) == 3

    # Sort the tree by name to have a predictable order for assertions
    tree.sort(key=lambda x: x.name)

    # Check the 'app' folder
    app_folder = tree[0]
    assert app_folder.name == "app"
    assert len(app_folder.children) == 1
    assert app_folder.children[0].name == "api.py"

    # Check the 'core' folder
    core_folder = tree[1]
    assert core_folder.name == "core"
    assert len(core_folder.children) == 2
    # Sort children for predictable order
    core_folder.children.sort(key=lambda x: x.name)
    assert core_folder.children[0].name == "post.py"
    assert core_folder.children[1].name == "user.py"

    # Check for main.py at the root
    main_file = tree[2]
    assert main_file.name == "main.py"
    assert len(main_file.children) == 0


# src/backend/tests/unit/parser/analyzer/simple_project
