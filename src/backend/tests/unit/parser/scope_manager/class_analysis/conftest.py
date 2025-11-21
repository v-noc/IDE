import pytest
from app.core.parser.scope_manager.manger import ScopeManager
from app.core.parser.scope_manager.storage.models import ScopeType, SymbolType


@pytest.fixture
def populated_manager(manager, root_scope_id):
    """
    Provides a ScopeManager instance populated with a class hierarchy:
    - class Animal:
        - def wake_up(self)
        - def speak(self)
    - class Dog(Animal):
        - def speak(self)  # override

    Properly sets up inheritance relationships in the database.
    """

    animal_scope_id = manager.enter_scope(
        name="Animal", scope_type=ScopeType.CLASS)

    # Add wake_up method
    manager.enter_scope(name="wake_up", scope_type=ScopeType.FUNCTION)
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()

    # Add speak method
    manager.enter_scope(name="speak", scope_type=ScopeType.FUNCTION)
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()

    # Exit Animal class
    manager.exit_scope()

    # Get Animal symbol and mark it has no base classes
    animal_symbol = manager.repo.symbols.get_by_name_in_scope(
        "Animal", root_scope_id)
    manager.repo.symbols.add_to_symbol_attrs(
        animal_symbol.id, 'base_classes', [])

    # --- Define Dog(Animal) class ---
    manager.exit_scope()
    dog_scope_id = manager.enter_scope(name="Dog", scope_type=ScopeType.CLASS)

    # Add speak method (override)
    manager.enter_scope("speak", ScopeType.FUNCTION)
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()

    # Exit Dog class
    manager.exit_scope()

    # Get Dog symbol and set its base classes
    dog_symbol = manager.repo.symbols.get_by_name_in_scope(
        "Dog", root_scope_id)
    manager.repo.symbols.add_to_symbol_attrs(
        dog_symbol.id, 'base_classes', ["__main__.Animal"])

    # Calculate MRO for both classes
    mro_calculator.calculate_all()

    yield manager
    manager.close()
