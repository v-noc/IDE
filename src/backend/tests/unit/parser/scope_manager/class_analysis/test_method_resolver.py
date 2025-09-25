
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
