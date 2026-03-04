import shutil
from pathlib import Path

import pytest
import pytest_asyncio

from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.repository import Repositories
from app.core.schemas.tree import CallTreeNode, FileTreeNode
from app.core.services.project_service import ProjectService

SAMPLES_PATH = Path(__file__).parent / "sample_class"
PROJECT_PATH = SAMPLES_PATH
PROJECT_NAME = "sample_class"


@pytest_asyncio.fixture
async def setup_project(tmp_path, empty_project_uow):
    project_path = tmp_path / "project"
    shutil.copytree(PROJECT_PATH, project_path)

    project_service = ProjectService(empty_project_uow)

    project_node = await project_service.create(
        PROJECT_NAME, "Test Project", str(project_path)
    )
    empty_project_uow.project = project_node

    yield project_node, empty_project_uow
    await project_service.delete(project_node.id)
    shutil.rmtree(project_path)


@pytest.mark.asyncio
async def test_class_analysis(setup_project):
    project_node, project_uow = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        uow=project_uow,
    )
    await orchestrator.resync()

    project_service = ProjectService(project_uow)

    children = await project_service.get_children()
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
        (call for call in module_level_calls if call.name == "greet"),
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
        (call for call in greet_call_children if call.name == "call_back"),
        None,
    )
    assert callback_in_greet is not None
    assert callback_in_greet.target.qname == "sample_class.main.call_back"

    # Test 'super().greet()' call within 'greet'
    super_greet_in_greet = next(
        (call for call in greet_call_children if call.name == "greet"),
        None,
    )
    assert super_greet_in_greet is not None
    assert super_greet_in_greet.target.qname == "sample_class.main.Parent.greet"
