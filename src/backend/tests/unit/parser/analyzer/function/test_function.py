from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import AnyTreeNode

from pathlib import Path
from typing import List

from app.core.services.function_service import FunctionService


current_file_path = Path(__file__).resolve()
print("Current file path:", current_file_path)

# Get the directory of the current file
current_dir = current_file_path.parent
PROJECT_PATH = Path(current_dir, "./simple_function").absolute()


def find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next((node for node in nodes if node.name == name), None)


def test_function_get_code(arangodb_client):

    builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        ignore_file_name=None,
        db=arangodb_client
    )
    builder.build(
        "Protector", "Protector is a tool for protecting your code.")

    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = proj_service.get_all()

    children = proj_service.get_children(project[0].id)

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
    snippet = func_service.get_code(factory_func.id)

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


def test_function_collector(arangodb_client):

    builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        project_node=None,
        db=arangodb_client
    )
    builder.build(
        "Protector", "Protector is a tool for protecting your code.")

    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)

    project = project_service.get_all()

    children = project_service.get_children(project[0].id)
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
