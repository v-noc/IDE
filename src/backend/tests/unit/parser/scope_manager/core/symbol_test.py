import pytest
from app.core.parser.scope_manager.storage.models import SymbolType


def test_symbol_creation(sample_symbol_id, child_scope_id, repo):
    """Test the basic creation of a Symbol."""

    symbol = repo.symbols.get_by_id(sample_symbol_id)
    scope = repo.scopes.get_by_id(child_scope_id)

    print(f"symbol: {symbol}")
    print(f"scope: {scope} {child_scope_id}")

    assert symbol.name == "my_var"
    assert symbol.symbol_type == SymbolType.VARIABLE
    assert symbol.defining_scope_id == scope.id
    assert symbol.assigned_to_id is None  # Not assigned yet
    # assert not sample_symbol.assigned_from


def test_assign_to(manager, sample_symbol_id):
    """Test the assign_to method."""
    another_symbol = manager.define_symbol(
        name="another_var", symbol_type=SymbolType.VARIABLE)
    manager.writer.assignment_writer.assign_symbol(
        sample_symbol_id, another_symbol.id)
    sample_symbol = manager.repo.symbols.get_by_id(sample_symbol_id)
    assert sample_symbol.assigned_to_id == another_symbol.id
    # assert sample_symbol in another_symbol.assigned_from


def test_resolve_immediate(manager, sample_symbol_id, child_scope_id):
    """Test the resolve_assignment functionality via AssignmentResolver."""
    # When not assigned, should return None (no assignment to follow)

    result = manager.resolver.assignment_resolver.resolve_assignment(
        sample_symbol_id)
    assert result.id == sample_symbol_id  # Returns self when no assignment

    # When assigned, resolves to the target
    manager.current_scope_id = child_scope_id
    target = manager.define_symbol("target_var", SymbolType.VARIABLE)
    manager.writer.assignment_writer.assign_symbol(
        sample_symbol_id, target.id)

    immediate = manager.resolver.assignment_resolver.resolve_assignment(
        sample_symbol_id)
    assert immediate.id == target.id  # Resolves to target


def test_resolve_final(sample_symbol, child_scope, code_position, symbol_table):
    """Test the resolve_final method for a chain of assignments."""
    var1 = sample_symbol
    var2 = Symbol(name="var2", symbol_type=SymbolType.VARIABLE,
                  defining_scope_id=child_scope.id, code_position=code_position)
    func_symbol = Symbol(name="my_func", symbol_type=SymbolType.FUNCTION,
                         defining_scope_id=child_scope.id, code_position=code_position)
    var2.bind_table(sample_symbol._table)
    func_symbol.bind_table(sample_symbol._table)
    symbol_table.save_symbol(var2)
    symbol_table.save_symbol(func_symbol)

    var1.assign_to(var2)
    var2.assign_to(func_symbol)

    # Resolves through the chain to the final function symbol
    assert var1.resolve_final() == func_symbol
    assert var2.resolve_final() == func_symbol
    # A function symbol resolves to itself
    assert func_symbol.resolve_final() == func_symbol


def test_resolve_final_circular_dependency(sample_symbol, child_scope, code_position, symbol_table):
    """Test that resolve_final detects circular dependencies."""
    var1 = sample_symbol
    var2 = Symbol(name="var2", symbol_type=SymbolType.VARIABLE,
                  defining_scope_id=child_scope.id, code_position=code_position)
    var2.bind_table(sample_symbol._table)
    symbol_table.save_symbol(var2)

    var1.assign_to(var2)
    var2.assign_to(var1)  # Circular assignment

    with pytest.raises(RecursionError, match="Circular assignment detected"):
        var1.resolve_final()
