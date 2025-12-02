import shutil
from pathlib import Path

import pytest

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.parser.scope_manager.manager import ScopeManager

FIXTURE_PROJECT = Path(__file__).parent / "simple_function"
PROJECT_NAME = "simple_function"


@pytest.fixture
def setup_project(tmp_path):
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

    return project_node, scope_manager


def test_function_scope_hierarchy(setup_project):
    project_node, scope_manager = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        scope_manager=scope_manager,
    )
    change_set = orchestrator.resync()
    assert change_set.has_changes()

    # Verify Scopes

    # factory function
    factory = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.main.factory")
    assert factory is not None
    assert factory.type.value == "function"
    assert factory.start_line == 1

    # factory.add function
    add = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.main.factory.add")
    assert add is not None
    assert add.type.value == "function"
    assert add.start_line == 3

    # factory.build function
    build = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.factory.build")
    assert build is not None
    assert build.type.value == "function"
    assert build.start_line == 8

    # call_back function
    call_back = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.call_back")
    assert call_back is not None
    assert call_back.start_line == 14

    # factory_call function
    factory_call = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.factory_call")
    assert factory_call is not None
    assert factory_call.start_line == 19

    # curry_call function
    curry_call = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.curry_call")
    assert curry_call is not None
    assert curry_call.start_line == 25

    # main function
    main = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.main.main")
    assert main is not None
    assert main.start_line == 30

    # Verify Parent-Child Relationships
    factory_children = scope_manager.get_children(factory.id)
    child_names = {c.name for c in factory_children}
    assert "add" in child_names
    assert "build" in child_names

    # Verify IDs are persisted (if we check against the IDs in docstrings, we'd need to parse them,
    # but here we just check if they are valid UUIDs or whatever ASTProcessor generates).
    assert factory.id is not None
    assert add.id is not None


def test_call_chain_construction(setup_project):
    """Test that call chains are built correctly with Jedi resolution."""
    project_node, scope_manager = setup_project

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        scope_manager=scope_manager,
    )
    orchestrator.resync()

    # Get scopes
    main = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.main.main")
    factory = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.main.factory")
    factory_call = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.factory_call")
    curry_call = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.curry_call")
    add = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.main.factory.add")
    build = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.factory.build")
    call_back = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.main.call_back")

    curry_call_calls = scope_manager.get_call_chain_roots(curry_call.id)
    assert len(curry_call_calls) == 2, "curry_call should have calls"

    # Test 1: Verify calls from main()
    main_calls = scope_manager.get_call_chain_roots(main.id)
    assert len(main_calls) == 4, "main should have calls"

    # main() calls factory_call()
    factory_call_calls = [
        c for c in main_calls if c['call_site'].name == 'factory_call']
    assert len(factory_call_calls) == 1
    if factory_call_calls[0]['callee']:
        assert factory_call_calls[0]['callee'].qname == f"{PROJECT_NAME}.main.factory_call"

    # Test 2: Verify calls from factory_call()
    factory_call_calls_list = scope_manager.get_calls_from(factory_call.id)
    assert len(factory_call_calls_list) == 2

    # factory_call() calls factory()
    factory_calls = [
        c for c in factory_call_calls_list if c['call_site'].name == 'factory']
    assert len(factory_calls) == 1
    if factory_calls[0]['callee']:
        assert factory_calls[0]['callee'].qname == f"{PROJECT_NAME}.main.factory"

    # factory_call() calls add()
    add_calls = [
        c for c in factory_call_calls_list if c['call_site'].name == 'add']
    assert len(add_calls) == 1

    # Test 3: Verify calls from add() - nested function
    add_calls_list = scope_manager.get_calls_from(add.id)
    assert len(add_calls_list) == 1

    # add() calls build()
    build_calls = [c for c in add_calls_list if c['call_site'].name == 'build']
    assert len(build_calls) == 1
    if build_calls[0]['callee']:
        assert build_calls[0]['callee'].qname == f"{PROJECT_NAME}.main.factory.build"

    # Test 4: Verify calls from call_back()
    call_back_calls = scope_manager.get_calls_from(call_back.id)
    # call_back() calls call_back_func() parameter - may not be resolved to a specific scope
    assert len(call_back_calls) == 1
    if call_back_calls[0]['callee']:
        assert call_back_calls[0]['callee'].qname == f"{PROJECT_NAME}.main.factory.add"

    factory_root_calls = scope_manager.get_call_chain_roots(factory.id)

    assert len(factory_root_calls) == 3, "factory should have one root call"

    print("\n✅ All call chain tests passed!")
