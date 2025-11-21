import pytest
from app.core.parser.scope_manager.manger import ScopeManager
from app.core.parser.scope_manager.storage.repository.repos import ScopeManagerRepository
from app.core.parser.scope_manager.storage.models import SymbolType, ScopeType


@pytest.fixture
def manager():
    """Provides a ScopeManager with in-memory database for testing."""
    mgr = ScopeManager()
    yield mgr
    mgr.close()


@pytest.fixture
def root_scope_id(manager):
    """Provides a root scope ID for testing."""
    scope = manager.create_root_scope(name="__main__", file_path="test.py")
    return scope.id


@pytest.fixture
def child_scope_id(manager, root_scope_id):
    """Provides a child function scope ID attached to the root scope."""
    # Make sure we're in root scope
    manager.current_scope_id = root_scope_id

    # Enter function scope
    scope = manager.enter_scope(
        "my_function", ScopeType.FUNCTION, "test.py")
    return scope.id


@pytest.fixture
def sample_symbol_id(manager, child_scope_id):
    """Provides a sample symbol ID within the child scope."""
    # Make sure we're in child scope
    manager.current_scope_id = child_scope_id

    # Define a variable
    symbol = manager.define_symbol("my_var", SymbolType.VARIABLE)
    return symbol.id


@pytest.fixture
def repo(manager):
    """Provides a repository for direct database access in tests."""
    with manager.db_session as session:

        repo = ScopeManagerRepository(session)
        yield repo
        session.commit()
