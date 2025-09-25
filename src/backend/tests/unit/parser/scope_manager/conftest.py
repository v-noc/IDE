import pytest
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.core import Scope, ScopeType, SymbolType
from app.core.model.properties import CodePosition


@pytest.fixture
def code_position():
    """Provides a default CodePosition."""
    return CodePosition(line_no=1, col_offset=0, end_line_no=1, end_col_offset=10)


@pytest.fixture
def root_scope(code_position):
    """Provides a root scope for testing."""
    return Scope(name="__main__", scope_type=ScopeType.MODULE, code_position=code_position)


@pytest.fixture
def child_scope(root_scope, code_position):
    """Provides a child scope attached to the root scope."""
    scope = Scope(name="my_function", scope_type=ScopeType.FUNCTION,
                  code_position=code_position)
    root_scope.add_child_scope(scope)
    return scope


@pytest.fixture
def sample_symbol(child_scope, code_position):
    """Provides a sample symbol within the child scope."""
    symbol = Symbol(
        name="my_var",
        symbol_type=SymbolType.VARIABLE,
        defining_scope=child_scope,
        code_position=code_position
    )
    child_scope.add_symbol(symbol)
    return symbol
