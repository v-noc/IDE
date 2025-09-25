
def test_mro_calculation(populated_scope_manager):
    """
    Tests that the MRO is calculated correctly for a simple hierarchy.
    """
    # MRO for Animal should be [Animal, object]
    animal_mro = populated_scope_manager.get_mro('__main__.Animal')
    assert animal_mro == ['__main__.Animal']

    # MRO for Dog should be [Dog, Animal, object]
    dog_mro = populated_scope_manager.get_mro('__main__.Dog')
    assert dog_mro == ['__main__.Dog', '__main__.Animal']
