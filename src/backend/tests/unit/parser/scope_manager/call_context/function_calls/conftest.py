import pytest
from app.core.parser.scope_manager.manager import ScopeManager


@pytest.fixture
def scope_manager() -> ScopeManager:
    """
    Provides a clean ScopeManager instance with a root scope for each test.
    """
    manager = ScopeManager()
    manager.create_root_scope("__main__")
    return manager
