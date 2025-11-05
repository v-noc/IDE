import pytest
from app.core.parser.scope_manager.core.symbol import Symbol, SymbolType


def test_symbol_creation(sample_symbol, child_scope):
    """Test the basic creation of a Symbol."""
    assert sample_symbol.name == "my_var"
    assert sample_symbol.symbol_type == SymbolType.VARIABLE
    assert sample_symbol.defining_scope.id == child_scope.id
    assert not sample_symbol.assigned_to
    # assert not sample_symbol.assigned_from


def test_assign_to(sample_symbol, child_scope, code_position, symbol_table):
    """Test the assign_to method."""
    another_symbol = Symbol(
        name="another_var",
        symbol_type=SymbolType.VARIABLE,
        defining_scope_id=child_scope.id,
        code_position=code_position
    )
    another_symbol.bind_table(sample_symbol._table)
    symbol_table.save_symbol(another_symbol)
    sample_symbol.assign_to(another_symbol)
    assert sample_symbol.assigned_to.id == another_symbol.id
    # assert sample_symbol in another_symbol.assigned_from


def test_resolve_immediate(sample_symbol, child_scope, code_position, symbol_table):
    """Test the resolve_immediate method."""
    # When not assigned, resolves to self
    assert sample_symbol.resolve_immediate() == sample_symbol

    # When assigned, resolves to the target
    target_symbol = Symbol(
        name="target_var",
        symbol_type=SymbolType.VARIABLE,
        defining_scope_id=child_scope.id,
        code_position=code_position
    )
    target_symbol.bind_table(sample_symbol._table)
    symbol_table.save_symbol(target_symbol)
    sample_symbol.assign_to(target_symbol)
    assert sample_symbol.resolve_immediate() == target_symbol


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
