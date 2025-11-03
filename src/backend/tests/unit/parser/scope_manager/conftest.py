import pytest
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.core import Scope, ScopeType, SymbolType, Symbol
from app.core.model.properties import CodePosition
from app.core.parser.scope_manager.storage.symbol_table import SymbolTable


@pytest.fixture
def code_position():
    """Provides a default CodePosition."""
    return CodePosition(line_no=1, col_offset=0, end_line_no=1, end_col_offset=10)


@pytest.fixture
def symbol_table():
    """Provides a symbol table for testing."""
    return SymbolTable("test_symbol_table")


@pytest.fixture
def root_scope(symbol_table):
    """Provides a root scope for testing."""
    scope = Scope(name="__main__", scope_type=ScopeType.MODULE)
    scope.bind_table(symbol_table)
    print("Saving root scope", symbol_table)
    symbol_table.save_scope(scope)
    return scope


@pytest.fixture
def child_scope(root_scope, symbol_table):
    """Provides a child scope attached to the root scope."""
    scope = Scope(name="my_function", scope_type=ScopeType.FUNCTION)
    scope.bind_table(symbol_table)
    print("Saving child scope", root_scope)
    root_scope.bind_table(symbol_table)
    symbol_table.save_scope(scope)
    root_scope.add_child_scope(scope)
    return scope


@pytest.fixture
def sample_symbol(child_scope, symbol_table):
    """Provides a sample symbol within the child scope."""
    symbol = Symbol(
        name="my_var",
        symbol_type=SymbolType.VARIABLE,
        defining_scope_id=child_scope.id,
    )
    symbol.bind_table(symbol_table)
    symbol_table.save_symbol(symbol)
    child_scope.add_symbol(symbol)

    return symbol
