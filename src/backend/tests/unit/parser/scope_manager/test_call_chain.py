
import pytest
import tempfile
import shutil
from app.core.parser.scope_manager import ScopeManager, ScopeType


@pytest.fixture
def temp_manager():
    """Create a temporary ScopeManager for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/test_db"
    manager = ScopeManager(project_name="test_project", db_path=db_path)
    manager.initialize()
    yield manager

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_call_chain_creation(temp_manager):
    """Test creating a call chain."""
    # Create scopes
    func_a = temp_manager.create_scope(
        name="func_a",
        qname="file.py::func_a",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=1,
        start_col=0,
        end_line=5,
        end_col=0,
    )

    func_b = temp_manager.create_scope(
        name="func_b",
        qname="file.py::func_b",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=15,
        end_col=0,
    )

    func_c = temp_manager.create_scope(
        name="func_c",
        qname="file.py::func_c",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=20,
        start_col=0,
        end_line=25,
        end_col=0,
    )

    # Create call chain: func_a -> func_b -> func_c
    call1 = temp_manager.create_call(
        caller_id=func_a.id,
        callee_id=func_b.id,
        line=3,
        col=4,
    )

    call2 = temp_manager.create_call(
        caller_id=func_b.id,
        callee_id=func_c.id,
        line=12,
        col=4,
        prev_call_site_id=call1.id,  # Chain to previous call
    )

    # Get the chain starting from call1
    chain = temp_manager.get_call_chain(call1.id)
    assert len(chain) == 2
    assert chain[0].id == call1.id
    assert chain[1].id == call2.id


def test_call_chain_roots(temp_manager):
    """Test getting call chain roots."""
    # Create scopes
    func_a = temp_manager.create_scope(
        name="func_a",
        qname="file.py::func_a",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=1,
        start_col=0,
        end_line=5,
        end_col=0,
    )

    func_b = temp_manager.create_scope(
        name="func_b",
        qname="file.py::func_b",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=15,
        end_col=0,
    )

    func_c = temp_manager.create_scope(
        name="func_c",
        qname="file.py::func_c",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=20,
        start_col=0,
        end_line=25,
        end_col=0,
    )

    # Create two chains
    # Chain 1: func_a -> func_b
    root1 = temp_manager.create_call(
        caller_id=func_a.id,
        callee_id=func_b.id,
        line=3,
        col=4,
    )

    temp_manager.create_call(
        caller_id=func_b.id,
        callee_id=func_c.id,
        line=12,
        col=4,
        prev_call_site_id=root1.id,
    )

    # Chain 2: separate root
    root2 = temp_manager.create_call(
        caller_id=func_c.id,
        callee_id=func_a.id,
        line=22,
        col=4,
    )

    # Get all roots
    roots = temp_manager.get_call_chain_roots()
    root_ids = [r.id for r in roots]

    assert len(roots) == 2
    assert root1.id in root_ids
    assert root2.id in root_ids


def test_call_chain_roots_filtered_by_target_scope(temp_manager):
    """Test getting call chain roots that pass through a given target scope (callee)."""
    # Create scopes
    func_a = temp_manager.create_scope(
        name="func_a",
        qname="file.py::func_a",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=1,
        start_col=0,
        end_line=5,
        end_col=0,
    )

    func_b = temp_manager.create_scope(
        name="func_b",
        qname="file.py::func_b",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=15,
        end_col=0,
    )

    func_c = temp_manager.create_scope(
        name="func_c",
        qname="file.py::func_c",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=20,
        start_col=0,
        end_line=25,
        end_col=0,
    )

    # Chain 1: func_a -> func_b -> func_c
    root1 = temp_manager.create_call(
        caller_id=func_a.id,
        callee_id=func_b.id,
        line=3,
        col=4,
    )

    temp_manager.create_call(
        caller_id=func_b.id,
        callee_id=func_c.id,
        line=12,
        col=4,
        prev_call_site_id=root1.id,
    )

    # Chain 2: func_c -> func_a
    root2 = temp_manager.create_call(
        caller_id=func_c.id,
        callee_id=func_a.id,
        line=22,
        col=4,
    )

    # Filter by calls targeting func_b
    roots_to_b = temp_manager.get_call_chain_roots(target_scope_id=func_b.id)
    root_ids_to_b = {r.id for r in roots_to_b}
    assert root_ids_to_b == {root1.id}

    # Filter by calls targeting func_c
    roots_to_c = temp_manager.get_call_chain_roots(target_scope_id=func_c.id)
    root_ids_to_c = {r.id for r in roots_to_c}
    assert root_ids_to_c == {root1.id}

    # Filter by calls targeting func_a (only chain 2 targets func_a)
    roots_to_a = temp_manager.get_call_chain_roots(target_scope_id=func_a.id)
    root_ids_to_a = {r.id for r in roots_to_a}
    assert root_ids_to_a == {root2.id}
