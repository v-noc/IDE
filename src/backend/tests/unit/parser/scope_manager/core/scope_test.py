from app.core.parser.scope_manager.storage.models import ScopeType, SymbolType


def test_scope_creation(manager, root_scope_id):
    """Test the basic creation of a Scope."""
    scope = manager.repo.scopes.get_by_id(root_scope_id)

    assert scope.name == "__main__"
    assert scope.scope_type == ScopeType.PROJECT
    assert scope.parent_id is None

    assert not scope.children
    assert not scope.symbols


def test_add_child_scope(manager, root_scope_id, child_scope_id):
    """Test adding a child scope to a parent scope."""
    child = manager.repo.scopes.get_by_id(child_scope_id)
    root = manager.repo.scopes.get_by_id(root_scope_id)

    # Verify parent-child relationship
    assert child.parent_id == root.id

    # Verify we can get children
    children = manager.repo.scopes.get_children(root.id)
    assert len(children) > 0
    assert any(c.id == child_scope_id for c in children)


def test_add_symbol(manager, child_scope_id, sample_symbol_id):
    """Test adding a symbol to a scope."""
    child = manager.repo.scopes.get_by_id(child_scope_id)

    symbol = manager.repo.symbols.get_by_id(sample_symbol_id)

    for s in child.symbols:
        assert s.name == symbol.name
    assert symbol.defining_scope.id == child.id


def test_scope_qualified_name(manager, root_scope_id):
    """Test qualified name generation for nested scopes."""
    # Create root > module > function

    manager.enter_scope("MyClass", ScopeType.CLASS, "test.py")

    method = manager.enter_scope("my_method", ScopeType.FUNCTION, "test.py")

    # Get scope chain
    chain = manager.repo.scopes.get_scope_chain(method.id)

    # Should be [method, class, root]
    assert len(chain) == 3
    assert chain[0].name == "my_method"
    assert chain[1].name == "MyClass"
    assert chain[2].name == "__main__"


def test_symbol_lookup_in_scope(manager, root_scope_id):
    """Test looking up symbols by name in scope."""
    # Create a function in root scope

    func = manager.enter_scope("greet", ScopeType.FUNCTION, "test.py")

    manager.exit_scope()

    # The function scope has a symbol in root
    func_symbol = manager.repo.symbols.get_by_name_in_scope(
        "greet", root_scope_id)

    assert func_symbol is not None
    assert func_symbol.name == "greet"
    assert func_symbol.symbol_type == SymbolType.FUNCTION
    assert func_symbol.defines_scope_id == func.id
