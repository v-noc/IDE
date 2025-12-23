import shutil
from pathlib import Path
from typing import List

import pytest
import pytest_asyncio

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import AnyTreeNode
from app.core.services.function_service import FunctionService

FIXTURE_PROJECT = Path(__file__).parent / "simple_function"
PROJECT_NAME = "simple_function"


@pytest_asyncio.fixture
async def setup_project(tmp_path, arangodb_client):
    project_path = tmp_path / "project"
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
    repos = Repositories(arangodb_client)
    await repos.ensure_collections()
    project_service = ProjectService(repos)
    project_node = await project_service.create_node(project_node)

    return project_node, scope_manager, arangodb_client


def find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next((node for node in nodes if node.qname.split('.')[-1] == name), None)


@pytest.mark.asyncio
async def test_function_get_code(setup_project):
    project_node, scope_manager, arangodb_client = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=arangodb_client,
        scope_manager=scope_manager,
    )
    await orchestrator.resync()

    repos = Repositories(arangodb_client)

    proj_service = ProjectService(repos)
    project = await proj_service.get_all()

    children = await proj_service.get_children(project[0].id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    assert tree, "No tree nodes built"

    file_node = tree[0]
    # Pick a deterministic function by name from simple_function/main.py
    factory_func = next(
        (
            c
            for c in file_node.children
            if (
                getattr(c, 'node_type', '') == 'function'
                and c.name == 'factory'
            )
        ),
        None,
    )
    assert factory_func is not None, (
        "No 'factory' function node found"
    )

    func_service = FunctionService(repos)
    snippet = await func_service.get_code(factory_func.id)

    assert snippet is not None, "get_code returned None"
    assert 'code' in snippet, "snippet missing 'code' field"
    assert snippet['name'] == 'factory'
    assert isinstance(snippet['code'], str)
    assert len(snippet['code']) > 0

    code = snippet['code']
    # Basic content checks aligned with simple_function/main.py
    assert 'def factory' in code
    assert 'def add' in code
    assert 'def build' in code
    assert 'return add' in code


@pytest.mark.asyncio
async def test_function_collector(setup_project):
    project_node, scope_manager, arangodb_client = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=arangodb_client,
        scope_manager=scope_manager,
    )

    await orchestrator.resync()

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    project = await project_service.get_all()

    children = await project_service.get_children(project[0].id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    # 1. Project structure assertions
    assert len(tree) == 1

    file_node = tree[0]

    # 2. Function definitions in main.py
    func_names = sorted([child.name for child in file_node.children])

    expected_func_names = sorted(
        ['factory', 'call_back', 'factory_call', 'curry_call', 'main'])
    for func_name in func_names:
        assert func_name in expected_func_names

    main_func = find_node_by_name(file_node.children, 'main')

    factory_func = find_node_by_name(file_node.children, 'factory')
    call_back_func = find_node_by_name(file_node.children, 'call_back')
    factory_call_func = find_node_by_name(
        file_node.children, 'factory_call')
    curry_call_func = find_node_by_name(file_node.children, 'curry_call')

    # 3. Assert functions and calls within `factory` function
    assert len(factory_func.children) == 2
    add_func = find_node_by_name(factory_func.children, 'add')
    build_func = find_node_by_name(factory_func.children, 'build')
    assert add_func is not None and build_func is not None
    assert len(add_func.children) == 1
    build_call = find_node_by_name(add_func.children, 'build')
    assert build_call is not None
    assert build_call.node_type == 'call'
    assert build_call.target.id == build_func.id

    # 4. Assert calls within `main` function
    assert len(main_func.children) == 4
    main_factory_call = find_node_by_name(main_func.children, 'factory_call')
    main_curry_call = find_node_by_name(main_func.children, 'curry_call')
    main_factory_assign = find_node_by_name(main_func.children, 'factory')
    main_call_back = find_node_by_name(main_func.children, 'call_back')

    # 4.1 Check `factory_call()` in `main`
    assert main_factory_call.target.id == factory_call_func.id
    children = [{child.name: child.node_type}
                for child in main_factory_call.children]

    assert len(main_factory_call.children) == 2
    inner_factory_call = find_node_by_name(
        main_factory_call.children, 'factory')
    inner_add_call = find_node_by_name(main_factory_call.children, 'add')
    assert inner_factory_call.target.id == factory_func.id
    assert inner_add_call.target.id == add_func.id
    assert len(inner_add_call.children) == 1
    final_build_call = find_node_by_name(inner_add_call.children, 'build')
    assert final_build_call.target.id == build_func.id

    # 4.2 Check `curry_call()` in `main`
    assert main_curry_call.target.id == curry_call_func.id
    assert len(main_curry_call.children) == 2
    curry_factory_call = find_node_by_name(
        main_curry_call.children, 'factory')
    curry_add_call = find_node_by_name(main_curry_call.children, 'add')
    assert curry_factory_call.target.id == factory_func.id

    assert curry_add_call.target.id == add_func.id
    assert len(curry_add_call.children) == 1
    final_build_call = find_node_by_name(curry_add_call.children, 'build')
    assert final_build_call.target.id == build_func.id

    # 4.3 Check `builder = factory()` in `main`
    assert main_factory_assign.target.id == factory_func.id

    # 4.4 Check `call_back(builder)` in `main`
    assert main_call_back.target.id == call_back_func.id
    assert len(main_call_back.children) == 1
    callback_add_call = find_node_by_name(main_call_back.children, 'add')
    assert callback_add_call.target.id == add_func.id
    assert len(callback_add_call.children) == 1
    final_build_call = find_node_by_name(callback_add_call.children, 'build')
    assert final_build_call.target.id == build_func.id

    # 6. Top-level `main()` call
    # This logic needs adjustment based on how you identify top-level calls.
    # Assuming the second 'main' is the call.
    all_main_nodes = [
        node for node in file_node.children if node.name == 'main']
    main_function_node = [
        node for node in all_main_nodes if node.node_type == 'function'][0]
    main_call_node = [
        node for node in all_main_nodes if node.node_type == 'call'][0]

    assert main_call_node is not None
    assert main_call_node.target.id == main_function_node.id
    # Also check the nested calls within this top-level `main` call.
    # The structure should be identical to the checks for `main_func`
    assert len(main_call_node.children) == 4
