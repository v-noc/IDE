
def test_mro_calculation_animal(populated_manager):
    """
    Tests that the MRO is calculated correctly for Animal class.
    Animal has no bases, so MRO should be [Animal].
    """

    # Get MRO for Animal
    animal_mro = populated_manager.resolver.inheritance_resolver.mro_calculator.get_mro(
        '__main__.Animal')

    # Animal should be first in its MRO
    assert animal_mro[0] == '__main__.Animal'
    # MRO should be just [Animal] since it has no bases
    assert len(animal_mro) == 1


def test_mro_calculation_dog(populated_manager):
    """
    Tests that the MRO is calculated correctly for Dog class.
    Dog(Animal), so MRO should be [Dog, Animal].
    """

    # Get MRO for Dog
    dog_mro = populated_manager.resolver.inheritance_resolver.mro_calculator.get_mro(
        '__main__.Dog')

    # Dog should be first
    assert dog_mro[0] == '__main__.Dog'
    # Animal should be second
    assert dog_mro[1] == '__main__.Animal'
    # MRO should be [Dog, Animal]
    assert len(dog_mro) == 2
    assert dog_mro == ['__main__.Dog', '__main__.Animal']


def test_mro_stored_in_symbol_attrs(populated_manager):
    """
    Tests that calculated MRO is stored in symbol.attrs['mro'] after calculation.
    """

    # Calculate MRO (this stores it in attrs)
    populated_manager.resolver.inheritance_resolver.mro_calculator.get_mro(
        '__main__.Dog')

    # Get Dog symbol
    dog_symbol = populated_manager.resolver.qname_resolver.resolve_qname(
        "__main__.Dog")

    # MRO should now be in attrs (was set by get_mro)
    print(dog_symbol.attrs)
    assert dog_symbol.attrs is not None
    assert 'mro' in dog_symbol.attrs

    # MRO should be correct
    stored_mro = dog_symbol.attrs['mro']
    print(stored_mro)
    assert stored_mro == ['__main__.Dog', '__main__.Animal']


def test_base_classes_stored(populated_manager):
    """
    Tests that base_classes are properly stored in symbol.attrs.
    """

    # Animal has no bases
    animal_symbol = populated_manager.resolver.qname_resolver.resolve_qname(
        "__main__.Animal")

    assert animal_symbol.attrs.get('base_classes', []) == []

    # Dog inherits from Animal
    dog_symbol = populated_manager.resolver.qname_resolver.resolve_qname(
        "__main__.Dog")
    assert dog_symbol.attrs['base_classes'] == ["__main__.Animal"]
    # Animal has no bases
    assert animal_symbol.attrs.get('base_classes', []) == []

    # Dog inherits from Animal
    assert dog_symbol.attrs['base_classes'] == ["__main__.Animal"]
