from app.core.parser.scope_manager.core.scope import Scope, ScopeType


def test_scope_creation(root_scope):
    """Test the basic creation of a Scope."""
    assert root_scope.name == "__main__"
    assert root_scope.scope_type == ScopeType.MODULE
    assert root_scope.parent_id is None
    assert not root_scope.children
    assert not root_scope.symbols


def test_add_child_scope(root_scope, child_scope):
    """Test adding a child scope to a parent scope."""
    assert child_scope.parent_id == root_scope.id
    assert "my_function" in root_scope.children
    assert root_scope.children["my_function"] == child_scope


def test_add_symbol(child_scope, sample_symbol):
    """Test adding a symbol to a scope."""
    assert "my_var" in child_scope.symbols
    assert child_scope.symbols["my_var"] == sample_symbol
    assert sample_symbol.defining_scope.id == child_scope.id


def test_add_wildcard_import(root_scope, child_scope, code_position):
    """Test adding wildcard import scopes."""
    module_scope1 = Scope(
        name="module1", scope_type=ScopeType.MODULE, code_position=code_position)
    module_scope2 = Scope(
        name="module2", scope_type=ScopeType.MODULE, code_position=code_position)

    root_scope.add_wildcard_import(module_scope1)
    assert root_scope.wildcard_import_scope_ids == [module_scope1.id]

    root_scope.add_wildcard_import(module_scope2)
    assert root_scope.wildcard_import_scope_ids == [
        module_scope1.id, module_scope2.id]

    # Test that re-adding a scope moves it to the end (last import wins)
    root_scope.add_wildcard_import(module_scope1)
    assert root_scope.wildcard_import_scope_ids == [
        module_scope2.id, module_scope1.id]
