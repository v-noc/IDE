import pytest
from app.core.parser.scope_manager.storage.models import SymbolType, ScopeType


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


def test_resolve_chain_final(manager, sample_symbol_id, child_scope_id):
    """Test the resolve_final method for a chain of assignments."""
    # Create assignment chain: var1 -> var2 -> func_symbol
    manager.current_scope_id = child_scope_id

    var2 = manager.define_symbol("var2", SymbolType.VARIABLE)
    func = manager.enter_scope("my_func", ScopeType.FUNCTION, "")
    manager.exit_scope()  # Back to child scope

    # Now get the function symbol (created in child scope when entering)

    func_symbol = manager.resolver.scope_resolver.resolve_name(
        "my_func", child_scope_id)
    assert func_symbol is not None
    func_symbol_id = func_symbol.id

    # Create chain: sample_symbol -> var2 -> func_symbol
    manager.writer.assignment_writer.assign_symbol(sample_symbol_id, var2.id)
    manager.writer.assignment_writer.assign_symbol(var2.id, func_symbol_id)

    # Resolve var1 (sample_symbol)
    final1 = manager.resolver.assignment_resolver.resolve_assignment(
        sample_symbol_id)
    assert final1.id == func_symbol_id

    # Resolve var2
    final2 = manager.resolver.assignment_resolver.resolve_assignment(var2.id)
    assert final2.id == func_symbol_id

    # Function symbol resolves to itself
    final3 = manager.resolver.assignment_resolver.resolve_assignment(
        func_symbol_id)
    assert final3.id == func_symbol_id


def test_resolve_final_circular_dependency(manager, sample_symbol_id, child_scope_id):
    """Test assignment resolver behavior with circular dependencies."""
    # Create another variable
    manager.current_scope_id = child_scope_id
    var2 = manager.define_symbol("var2", SymbolType.VARIABLE)

    # Create circular assignment: var1 -> var2 -> var1
    manager.writer.assignment_writer.assign_symbol(sample_symbol_id, var2.id)
    manager.writer.assignment_writer.assign_symbol(
        var2.id, sample_symbol_id)  # Circular!

    # Assignment resolver should handle this gracefully
    # (may return one of the symbols in the cycle or detect it)

    # The resolver should handle circular refs (exact behavior may vary)
    result = manager.resolver.assignment_resolver.resolve_assignment(
        sample_symbol_id)
    # May return None for circular refs, or one of the symbols
    assert result is None or result.id in [sample_symbol_id, var2.id]
