import shutil
from pathlib import Path

import pytest

from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.repository import Repositories
from app.core.schemas.tree import AnyTreeNode, CallTreeNode, FileTreeNode
from app.core.services.project_service import ProjectService

SAMPLES_PATH = Path(__file__).parent / "sample_class"
PROJECT_PATH = SAMPLES_PATH
PROJECT_NAME = "sample_class"


@pytest.fixture
def setup_project(tmp_path, arangodb_client):
    project_path = tmp_path / "sample_class"
    shutil.copytree(PROJECT_PATH, project_path)

    db_path = tmp_path / "db" / PROJECT_NAME
    db_path.parent.mkdir(parents=True, exist_ok=True)

    project_node = ProjectNode(
        name=PROJECT_NAME,
        path=str(project_path),
        qname=PROJECT_NAME,
        description="Protector is a tool for protecting your code.",
    )
    scope_manager = ScopeManager(PROJECT_NAME, db_path=str(db_path))
    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)
    project_node = project_service.create_node(project_node)

    return project_node, scope_manager, arangodb_client


def test_class_analysis(setup_project):
    project_node, scope_manager, arangodb_client = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=arangodb_client,
        scope_manager=scope_manager,
    )
    orchestrator.resync()

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    project = project_service.get_all()

    children = project_service.get_children(project[0].id)
    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    assert tree, "Tree should not be empty"
    main_py_node = tree[0]
    assert isinstance(main_py_node, FileTreeNode)
    assert main_py_node.name == "main"

    # Module-level calls
    module_level_calls = [
        node for node in main_py_node.children if isinstance(node, CallTreeNode)
    ]
    assert len(module_level_calls) == 2

    # Test 'child = Child(call_back)' call
    init_call = next(
        (call for call in module_level_calls if call.name == "Parent"),
        None,
    )
    # assert init_call is not None
    # assert init_call.target.qname == "protector.main.Parent.__init__"

    # Test 'wake_up' call within 'Child' instantiation
    # wake_up_in_init = next(
    #     (
    #         child
    #         for child in init_call.children
    #         if isinstance(child, CallTreeNode)
    #     ),
    #     None,
    # )
    # assert wake_up_in_init is not None
    # assert wake_up_in_init.name == "(GrandParent).wake_up"
    # assert (
    #     wake_up_in_init.target.qname == "protector.main.GrandParent.wake_up"
    # )

    # Test 'child.greet()' call
    greet_call = next(
        (
            call
            for call in module_level_calls
            if call.qname == "sample_class.main::sample_class.main.Child.greet"
        ),
        None,
    )
    assert greet_call is not None
    assert greet_call.target.qname == "sample_class.main.Child.greet"

    greet_call_children = [
        child for child in greet_call.children if isinstance(child, CallTreeNode)
    ]
    assert len(greet_call_children) == 2

    # Test 'self.callback()' call within 'greet'
    callback_in_greet = next(
        (call for call in greet_call_children if call.name == "callback"),
        None,
    )
    assert callback_in_greet is not None
    assert callback_in_greet.target.qname == "sample_class.main.call_back"

    # Test 'super().greet()' call within 'greet'
    super_greet_in_greet = next(
        (
            call
            for call in greet_call_children
            if call.qname == "sample_class.main.Child.greet::sample_class.main.Parent.greet"
        ),
        None,
    )
    assert super_greet_in_greet is not None
    assert super_greet_in_greet.target.qname == "sample_class.main.Parent.greet"
