from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import AnyTreeNode, CallTreeNode, FileTreeNode

from pathlib import Path
from typing import List


SAMPLES_PATH = Path(__file__).parent / "sample_class"
PROJECT_PATH = SAMPLES_PATH


def test_class_analysis(arangodb_client):
    graph_builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        ignore_file_name=None,
        db=arangodb_client,
    )
    graph_builder.build(
        "Protector", "Protector is a tool for protecting your code."
    )

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    project = project_service.get_all()

    children = project_service.get_children(project[0].id)
    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    assert tree, "Tree should not be empty"
    main_py_node = tree[0]
    assert isinstance(main_py_node, FileTreeNode)
    assert main_py_node.name == "main.py"

    # Module-level calls
    module_level_calls = [
        node
        for node in main_py_node.children
        if isinstance(node, CallTreeNode)
    ]
    assert len(module_level_calls) == 2

    # Test 'child = Child(call_back)' call
    init_call = next(
        (call for call in module_level_calls if call.name == "(Parent).__init__"),
        None,
    )
    assert init_call is not None
    assert init_call.target.qname == "protector.main.Parent.__init__"

    # Test 'wake_up' call within 'Child' instantiation
    wake_up_in_init = next(
        (
            child
            for child in init_call.children
            if isinstance(child, CallTreeNode)
        ),
        None,
    )
    assert wake_up_in_init is not None
    assert wake_up_in_init.name == "(GrandParent).wake_up"
    assert (
        wake_up_in_init.target.qname == "protector.main.GrandParent.wake_up"
    )

    # Test 'child.greet()' call
    greet_call = next(
        (call for call in module_level_calls if call.name == "(Child).greet"), None
    )
    assert greet_call is not None
    assert greet_call.target.qname == "protector.main.Child.greet"

    greet_call_children = [
        child
        for child in greet_call.children
        if isinstance(child, CallTreeNode)
    ]
    assert len(greet_call_children) == 2

    # Test 'self.callback()' call within 'greet'
    callback_in_greet = next(
        (
            call
            for call in greet_call_children
            if call.name == "call_back"
        ),
        None,
    )
    assert callback_in_greet is not None
    assert callback_in_greet.target.qname == "protector.main.call_back"

    # Test 'super().greet()' call within 'greet'
    super_greet_in_greet = next(
        (call for call in greet_call_children if call.name == "(Parent).greet"),
        None,
    )
    assert super_greet_in_greet is not None
    assert super_greet_in_greet.target.qname == "protector.main.Parent.greet"
