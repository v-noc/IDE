import pytest
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.storage.symbol_table import SymbolTable


@pytest.fixture
def symbol_table():
    """Provides a symbol table for testing."""
    return SymbolTable("test_symbol_table")


@pytest.fixture
def scope_manager() -> ScopeManager:
    """
    Provides a clean ScopeManager instance with a root scope for each test.
    """
    manager = ScopeManager(db_name="test_symbol_table")
    manager.create_root_scope("__main__")
    return manager
