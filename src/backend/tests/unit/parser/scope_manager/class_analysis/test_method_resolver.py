
def test_resolve_method_override(populated_manager):
    """
    Tests that `resolve_method` finds the overridden method in the subclass.
    """
    # Resolve 'speak' method on Dog class
    method_symbol = populated_manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        "__main__.Dog", "speak")

    assert method_symbol is not None
    assert method_symbol.name == 'speak'

    # Should be the one defined in Dog scope (override)
    defining_scope = populated_manager.repo.scopes.get_by_id(
        method_symbol.defining_scope_id)
    assert defining_scope.name == 'Dog'


def test_resolve_method_from_base(populated_manager):
    """
    Tests that `resolve_method` finds a method in the base class.
    """
    method_symbol_found = populated_manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        '__main__.Dog', 'wake_up')
    assert method_symbol_found is not None
    assert method_symbol_found.name == 'wake_up'
    assert method_symbol_found.defining_scope.name == 'Animal'


def test_resolve_super_call(populated_manager):
    """
    Tests that `resolve_super_call` finds the method in the superclass.
    """
    dog_speak_scope = populated_manager.resolver.qname_resolver.resolve_qname(
        '__main__.Dog.speak')

    # Resolve super().speak() from Dog context
    super_method_symbol = populated_manager.resolver.inheritance_resolver.method_resolver.resolve_super_call(
        '__main__.Dog', 'speak')

    assert super_method_symbol is not None
    assert super_method_symbol.name == 'speak'

    # Should be the one defined in Animal scope (parent)
    defining_scope = populated_manager.repo.scopes.get_by_id(
        super_method_symbol.defining_scope_id)
    assert defining_scope.name == 'Animal'


def test_resolve_nonexistent_method(populated_manager):
    """
    Tests that MethodResolver returns None for non-existent methods.
    """

    method_symbol = populated_manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        '__main__.Dog', 'nonexistent')

    assert method_symbol is None
