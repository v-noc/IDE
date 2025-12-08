import pytest
import tempfile
import shutil
from app.core.parser.scope_manager import (
    DBConnectionManager,
    ScopeRepository,
    ScopeModel,
    CallSiteModel,
    ScopeType,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = f"{temp_dir}/test_db"
    db_manager = DBConnectionManager(
        project_name="test_project", db_path=db_path)
    repo = ScopeRepository(db_manager)

    yield repo

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_create_and_get_scope(temp_db):
    """Test creating and retrieving a scope."""
    scope = ScopeModel(
        id="scope1",
        name="MyClass",
        qname="file.py::MyClass",
        type=ScopeType.CLASS,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=20,
        end_col=10,
    )

    temp_db.create_scope(scope)

    # Get by ID
    retrieved = temp_db.get_scope_by_id("scope1")
    assert retrieved is not None
    assert retrieved.name == "MyClass"
    assert retrieved.qname == "file.py::MyClass"

    # Get by qname
    retrieved_by_qname = temp_db.get_scope_by_qname("file.py::MyClass")
    assert retrieved_by_qname is not None
    assert retrieved_by_qname.id == "scope1"


def test_contains_relationship(temp_db):
    """Test creating CONTAINS relationship."""
    parent = ScopeModel(
        id="parent",
        name="MyClass",
        qname="file.py::MyClass",
        type=ScopeType.CLASS,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=30,
        end_col=0,
    )

    child = ScopeModel(
        id="child",
        name="my_method",
        qname="file.py::MyClass::my_method",
        type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=15,
        start_col=4,
        end_line=20,
        end_col=10,
    )

    temp_db.create_scope(parent)
    temp_db.create_scope(child)
    temp_db.create_contains_edge("parent", "child")

    # Verify both exist
    assert temp_db.get_scope_by_id("parent") is not None
    assert temp_db.get_scope_by_id("child") is not None


def test_call_site_creation(temp_db):
    """Test creating call site with relationships."""
    caller = ScopeModel(
        id="caller",
        name="func_a",
        qname="file.py::func_a",
        type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=10,
        start_col=0,
        end_line=15,
        end_col=0,
    )

    callee = ScopeModel(
        id="callee",
        name="func_b",
        qname="file.py::func_b",
        type=ScopeType.FUNCTION,
        file_path="/path/to/file.py",
        start_line=20,
        start_col=0,
        end_line=25,
        end_col=0,
    )

    call_site = CallSiteModel(
        id="call1",
        line=12,
        col=4,
    )

    temp_db.create_scope(caller)
    temp_db.create_scope(callee)
    temp_db.create_call_site("caller", "callee", call_site)

    # Verify scopes exist
    assert temp_db.get_scope_by_id("caller") is not None
    assert temp_db.get_scope_by_id("callee") is not None


def test_get_all_scopes(temp_db):
    """Test getting all scopes."""
    scope1 = ScopeModel(
        id="s1",
        name="Class1",
        qname="file.py::Class1",
        type=ScopeType.CLASS,
        file_path="/path/file.py",
        start_line=1,
        start_col=0,
        end_line=10,
        end_col=0,
    )

    scope2 = ScopeModel(
        id="s2",
        name="Class2",
        qname="file.py::Class2",
        type=ScopeType.CLASS,
        file_path="/path/file.py",
        start_line=20,
        start_col=0,
        end_line=30,
        end_col=0,
    )

    temp_db.create_scope(scope1)
    temp_db.create_scope(scope2)

    all_scopes = temp_db.get_all_scopes()
    assert len(all_scopes) == 2
    names = [s.name for s in all_scopes]
    assert "Class1" in names
    assert "Class2" in names
