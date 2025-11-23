import pytest

from app.core.parser.scope_manager.storage.models import ScopeType, SymbolType
from app.core.parser.scope_manager.manger import ScopeManager


@pytest.fixture
def class_hierarchy_manager(manager: ScopeManager, root_scope_id: str) -> ScopeManager:
    """
    Provides a ScopeManager with a pre-defined class hierarchy:
    - class Animal:
        - def __init__(self, name)
        - def speak(self)
        - def wake_up(self)
    - class Dog(Animal):
        - def __init__(self, name, breed)
        - def speak(self)  # Overrides Animal.speak
        - def bark(self)
    """
    # Define Animal class

    # --- Define Animal class ---
    manager.current_scope_id = manager.root_scope_id
    animal_scope_id = manager.enter_scope("Animal", ScopeType.CLASS, "test.py")

    # __init__ method
    manager.enter_scope("__init__", ScopeType.FUNCTION, "test.py")
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.define_symbol("name", SymbolType.PARAMETER)
    manager.exit_scope()

    # wake_up method
    manager.enter_scope("wake_up", ScopeType.FUNCTION, "test.py")
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()

    # speak method
    manager.enter_scope("speak", ScopeType.FUNCTION, "test.py")
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()

    manager.exit_scope()  # Exit Animal

    # --- Define Dog class (inherits from Animal) ---
    manager.current_scope_id = manager.root_scope_id
    dog_scope_id = manager.enter_scope("Dog", ScopeType.CLASS, "test.py")

    # speak method (override)
    manager.enter_scope("speak", ScopeType.FUNCTION, "test.py")
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()

    # bark method
    manager.enter_scope("bark", ScopeType.FUNCTION, "test.py")
    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()

    manager.exit_scope()  # Exit Dog

    # Get class symbols
    animal_symbol = manager.repo.symbols.get_by_name_in_scope(
        "Animal", manager.root_scope_id)
    dog_symbol = manager.repo.symbols.get_by_name_in_scope(
        "Dog", manager.root_scope_id)

    # Set base classes
    if not animal_symbol.attrs:
        animal_symbol.attrs = {}
    animal_symbol.attrs['base_classes'] = []

    if not dog_symbol.attrs:
        dog_symbol.attrs = {}
    dog_symbol.attrs['base_classes'] = ["__main__.Animal"]

    # Calculate MRO

    manager.resolver.inheritance_resolver.mro_calculator.calculate_all()

    yield manager
    manager.close()
