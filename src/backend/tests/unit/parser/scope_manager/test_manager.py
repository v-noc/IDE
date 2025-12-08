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

    yield manager

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_create_scope_with_manager(temp_manager):
    """Test creating scope using manager."""
    scope = temp_manager.create_scope(
        name="MyClass",
        qname="file.py::MyClass",
        scope_type=ScopeType.CLASS,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=20,
        end_col=0,
        base_classes=["BaseClass"],
        mro=["MyClass", "BaseClass", "object"],
    )

    assert scope.id is not None
    assert scope.name == "MyClass"
    assert scope.base_classes == ["BaseClass"]
    assert scope.mro == ["MyClass", "BaseClass", "object"]

    # Verify it was stored
    retrieved = temp_manager.get_scope(scope.id)
    assert retrieved is not None
    assert retrieved.base_classes == ["BaseClass"]
    assert retrieved.mro == ["MyClass", "BaseClass", "object"]


def test_hierarchy_management(temp_manager):
    """Test parent-child linking."""
    parent = temp_manager.create_scope(
        name="MyClass",
        qname="file.py::MyClass",
        scope_type=ScopeType.CLASS,
        file_path="/path/to/file.py",
        start_line=1,
        start_col=0,
        end_line=30,
        end_col=0,
    )

    child = temp_manager.create_scope(
        name="my_method",
        qname="file.py::MyClass::my_method",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=5,
        start_col=4,
        end_line=10,
        end_col=0,
    )

    temp_manager.link_parent_child(parent.id, child.id)

    # Get children
    children = temp_manager.get_children(parent.id)
    assert len(children) == 1
    assert children[0].name == "my_method"


def test_call_management(temp_manager):
    """Test call site creation and querying."""
    caller = temp_manager.create_scope(
        name="func_a",
        qname="file.py::func_a",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=1,
        start_col=0,
        end_line=5,
        end_col=0,
    )

    callee = temp_manager.create_scope(
        name="func_b",
        qname="file.py::func_b",
        scope_type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=15,
        end_col=0,
    )

    call_site = temp_manager.create_call(
        caller_id=caller.id,
        callee_id=callee.id,
        line=3,
        col=4,
    )

    assert call_site.id is not None

    # Get calls from caller
    calls_from = temp_manager.get_calls_from(caller.id)
    assert len(calls_from) == 1
    assert calls_from[0]["callee"].name == "func_b"

    # Get calls to callee
    calls_to = temp_manager.get_calls_to(callee.id)
    assert len(calls_to) == 1
    assert calls_to[0]["caller"].name == "func_a"


def test_delete_scope(temp_manager):
    """Test deleting a scope."""
    scope = temp_manager.create_scope(
        name="ToDelete",
        qname="file.py::ToDelete",
        scope_type=ScopeType.CLASS,
        file_path="/path/to/file.py",
        start_line=1,
        start_col=0,
        end_line=10,
        end_col=0,
    )

    temp_manager.delete_scope(scope.id)

    # Verify it's deleted
    retrieved = temp_manager.get_scope(scope.id)
    assert retrieved is None
