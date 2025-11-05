from fastapi.testclient import TestClient
from pathlib import Path
from app.core.parser.graph_builder import GraphBuilder
from app.core.services.project_service import ProjectService
from app.core.builder.tree_builder import TreeBuilder

current_file_path = Path(__file__).resolve()
print("Current file path:", current_file_path)

# Get the directory of the current file
current_dir = current_file_path.parent
PROJECT_PATH = Path(current_dir, "./sample_project").absolute()


def test_add_call(client: TestClient,  arangodb_client, create_repos):

    graph_builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(), ignore_file_name=None, db=arangodb_client
    )
    graph_builder.build("sample_import", "A test project for imports.")

    project_service = ProjectService(create_repos)
    project = project_service.get_all()[0]

    children = project_service.get_children(project.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    main_py_node = tree[0]

    assert main_py_node.name == "main.py"

    # Create call
    create_resp = client.post(
        f"/api/v1/calls/{main_py_node.key}/add-call",
        json={
            "name": "Call1",
            "description": "Desc",
            "callee_target_id": main_py_node.children[0].key,
        },
    )

    assert create_resp.status_code == 200
    assert create_resp.json() is not None

    children = project_service.get_children(project.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    main_py_node = tree[0]

    assert len(main_py_node.children) == 3


def test_remove_call(client: TestClient,  arangodb_client, create_repos):

    graph_builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(), ignore_file_name=None, db=arangodb_client
    )
    graph_builder.build("sample_import", "A test project for imports.")

    project_service = ProjectService(create_repos)
    project = project_service.get_all()[0]

    children = project_service.get_children(project.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    main_py_node = tree[0]

    assert main_py_node.name == "main.py"

    call_key = None

    for child in main_py_node.children:
        if child.node_type == "call":
            call_key = child.key
            break

    assert call_key is not None

    delete_resp = client.delete(
        f"/api/v1/calls/{call_key}/remove-call",
    )

    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"message": "Call removed successfully"}

    project = project_service.get_all()[0]

    children = project_service.get_children(project.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    main_py_node = tree[0]

    assert main_py_node.name == "main.py"
    assert len(main_py_node.children) == 1
    assert main_py_node.children[0].node_type == "function"
