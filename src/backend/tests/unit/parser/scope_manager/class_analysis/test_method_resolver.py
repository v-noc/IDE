
def test_resolve_method_override(populated_scope_manager):
    """
    Tests that `resolve_method` finds the overridden method in the subclass.
    """
    method_symbol = populated_scope_manager.resolve_method(
        '__main__.Dog', 'speak')
    print("method_symbol-->", method_symbol)
    assert method_symbol is not None
    assert method_symbol.name == 'speak'
    assert method_symbol.defining_scope.name == 'Dog'


def test_resolve_method_from_base(populated_scope_manager):
    """
    Tests that `resolve_method` finds a method in the base class.
    """
    # Temporarily add a method to Animal to test inheritance
    animal_scope = populated_scope_manager.get_scope_by_qname(
        '__main__.Animal')
    wake_up_scope = populated_scope_manager.enter_scope_by_scope(animal_scope).children.setdefault(
        'wake_up',
        type('Scope', (object,), {'name': 'wake_up', 'parent': animal_scope})()
    )

    method_symbol = populated_scope_manager.resolve_method(
        '__main__.Dog', 'wake_up')
    # This test is simplified because the fixture doesn't include wake_up.
    # A more robust test would add the method and symbol properly.
    # For now, we expect it to fail to resolve if not present.

    # Re-checking logic. `resolve_method` looks up symbols. Let's add one.
    from app.core.parser.scope_manager.core import Symbol, SymbolType
    wake_up_symbol = Symbol(name="wake_up", symbol_type=SymbolType.FUNCTION,
                            defining_scope=animal_scope, code_position=None)
    animal_scope.add_symbol(wake_up_symbol)

    method_symbol_found = populated_scope_manager.resolve_method(
        '__main__.Dog', 'wake_up')
    assert method_symbol_found is not None
    assert method_symbol_found.name == 'wake_up'
    assert method_symbol_found.defining_scope.name == 'Animal'


def test_resolve_super_call(populated_scope_manager):
    """
    Tests that `resolve_super_call` finds the method in the superclass.
    """
    dog_speak_scope = populated_scope_manager.get_scope_by_qname(
        '__main__.Dog.speak')

    super_method_symbol = populated_scope_manager.resolve_super_call(
        dog_speak_scope, 'speak')

    assert super_method_symbol is not None
    assert super_method_symbol.name == 'speak'
    assert super_method_symbol.defining_scope.name == 'Animal'
