import shutil
from pathlib import Path
from typing import List

import pytest
import pytest_asyncio

from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.repository import Repositories
from app.core.schemas.tree import AnyTreeNode
from app.core.services.function_service import FunctionService
from app.core.services.project_service import ProjectService

FIXTURE_PROJECT = Path(__file__).parent / "simple_function"
PROJECT_NAME = "simple_function"


@pytest_asyncio.fixture
async def setup_project(tmp_path, terminusdb_client):
    project_path = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project_path)

    repos = Repositories(terminusdb_client)

    project_service = ProjectService(repos)

    project_node = await project_service.create(PROJECT_NAME, "Test Project", str(project_path))

    yield project_node, repos, terminusdb_client
    await project_service.delete(project_node.id)
    shutil.rmtree(project_path)


def find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next((node for node in nodes if node.qname.split(".")[-1] == name), None)


def find_node(node):
    for child in node.children:
        if child.__class__.__name__ == "CallTreeNode":
            return child
        found = find_node(child)
        if found:
            return found
    return None


def find_node_by_qname(nodes: List[AnyTreeNode], qname: str):
    return next((node for node in nodes if getattr(node, "qname", None) == qname), None)


@pytest.mark.asyncio
async def test_function_get_code(setup_project):
    project_node, repos, arangodb_client = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=arangodb_client,
    )
    await orchestrator.resync()

    proj_service = ProjectService(repos)
    project = await proj_service.get_all()

    children = await proj_service.get_children(project[0].id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    assert tree, "No tree nodes built"

    file_node = tree[1]
    factory_qname = f"{file_node.qname}.factory"
    factory_func = find_node_by_qname(file_node.children, factory_qname)
    assert factory_func is not None, "No 'factory' function node found"

    func_service = FunctionService(repos)
    snippet = await func_service.get_code(factory_func.id)

    assert snippet is not None, "get_code returned None"
    assert "code" in snippet, "snippet missing 'code' field"
    assert snippet["name"] == "factory"
    assert isinstance(snippet["code"], str)
    assert len(snippet["code"]) > 0

    code = snippet["code"]
    # Basic content checks aligned with simple_function/main.py
    assert "def factory" in code
    assert "def add" in code
    assert "def build" in code
    assert "return add" in code


@pytest.mark.asyncio
async def test_function_collector(setup_project):
    project_node, repos, arangodb_client = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=arangodb_client,
    )

    await orchestrator.resync()

    project_service = ProjectService(repos)

    children = await project_service.get_children(project_node.db_name)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    # 1. Project structure assertions
    assert len(tree) == 2

    file_node = tree[0]

    # 2. Function definitions in main.py
    file_functions = [
        child for child in file_node.children if child.__class__.__name__ == "FunctionTreeNode"
    ]

    func_qnames = sorted([child.qname for child in file_functions])
    print(f"func_qnames {func_qnames}")

    expected_func_qnames = sorted(
        [
            f"{file_node.qname}.factory",
            f"{file_node.qname}.call_back",
            f"{file_node.qname}.factory_call",
            f"{file_node.qname}.curry_call",
            f"{file_node.qname}.main",
        ]
    )
    assert func_qnames == expected_func_qnames

    main_func = find_node_by_qname(
        file_node.children, f"{file_node.qname}.main")
    factory_func = find_node_by_qname(
        file_node.children, f"{file_node.qname}.factory")
    call_back_func = find_node_by_qname(
        file_node.children, f"{file_node.qname}.call_back"
    )
    factory_call_func = find_node_by_qname(
        file_node.children, f"{file_node.qname}.factory_call"
    )
    curry_call_func = find_node_by_qname(
        file_node.children, f"{file_node.qname}.curry_call"
    )

    calls = find_node(factory_func)

    # 3. Assert functions and calls within `factory` function
    assert len(factory_func.children) == 2
    add_func = find_node_by_qname(
        factory_func.children, f"{factory_func.qname}.add")
    build_func = find_node_by_qname(
        factory_func.children, f"{factory_func.qname}.build"
    )
    assert add_func is not None and build_func is not None

    print(f"add_func.children---: {len(children)}")
    assert len(
        add_func.children) == 1, f"add_func should have 1 child, {len(children)}"
    build_call = find_node_by_qname(
        add_func.children, f"{add_func.id}::{build_func.id}"
    )
    assert build_call is not None
    assert build_call.__class__.__name__ == "CallTreeNode"
    assert build_call.target.id == build_func.id

    # 4. Assert calls within `main` function
    assert len(main_func.children) == 4
    main_factory_call = find_node_by_qname(
        main_func.children, f"{main_func.id}::{factory_call_func.id}"
    )
    main_curry_call = find_node_by_qname(
        main_func.children, f"{main_func.id}::{curry_call_func.id}"
    )
    main_factory_assign = find_node_by_qname(
        main_func.children, f"{main_func.id}::{factory_func.id}"
    )
    main_call_back = find_node_by_qname(
        main_func.children, f"{main_func.id}::{call_back_func.id}"
    )

    # 4.1 Check `factory_call()` in `main`
    assert main_factory_call.target.id == factory_call_func.id
    # children = [{child.name: child.node_type}
    #             for child in main_factory_call.children]

    assert len(main_factory_call.children) == 2
    inner_factory_call = find_node_by_qname(
        main_factory_call.children, f"{main_factory_call.id}::{factory_func.id}"
    )
    inner_add_call = find_node_by_qname(
        main_factory_call.children, f"{main_factory_call.id}::{add_func.id}"
    )
    assert inner_factory_call.target.id == factory_func.id
    assert inner_add_call.target.id == add_func.id
    assert len(inner_add_call.children) == 1
    final_build_call = find_node_by_qname(
        inner_add_call.children, f"{inner_add_call.id}::{build_func.id}"
    )
    assert final_build_call.target.id == build_func.id

    # 4.2 Check `curry_call()` in `main`
    assert main_curry_call.target.id == curry_call_func.id
    assert len(main_curry_call.children) == 2
    curry_factory_call = find_node_by_qname(
        main_curry_call.children, f"{main_curry_call.id}::{factory_func.id}"
    )
    curry_add_call = find_node_by_qname(
        main_curry_call.children, f"{main_curry_call.id}::{add_func.id}"
    )
    assert curry_factory_call.target.id == factory_func.id

    assert curry_add_call.target.id == add_func.id
    assert len(curry_add_call.children) == 1
    final_build_call = find_node_by_qname(
        curry_add_call.children, f"{curry_add_call.id}::{build_func.id}"
    )
    assert final_build_call.target.id == build_func.id

    # 4.3 Check `builder = factory()` in `main`
    assert main_factory_assign.target.id == factory_func.id

    # 4.4 Check `call_back(builder)` in `main`
    assert main_call_back.target.id == call_back_func.id
    assert len(main_call_back.children) == 1
    callback_add_call = main_call_back.children[0]
    assert callback_add_call.target.id == add_func.id
    assert len(callback_add_call.children) == 1
    final_build_call = find_node_by_qname(
        callback_add_call.children,
        f"{callback_add_call.id}::{build_func.id}",
    )
    assert final_build_call.target.id == build_func.id

    # 6. Top-level `main()` call
    # This logic needs adjustment based on how you identify top-level calls.
    # Assuming the second 'main' is the call.
    main_function_node = find_node_by_qname(
        file_node.children, f"{file_node.qname}.main"
    )
    main_call_node = find_node_by_qname(
        file_node.children, f"{file_node.id}::{main_function_node.id}"
    )

    assert main_call_node is not None
    assert main_call_node.target.id == main_function_node.id
    # Also check the nested calls within this top-level `main` call.
    # The structure should be identical to the checks for `main_func`
    assert len(main_call_node.children) == 4
