import pytest
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.core import ScopeType, SymbolType


@pytest.fixture
def scope_manager() -> ScopeManager:
    """
    Provides a clean ScopeManager instance with a root scope for each test.
    """
    manager = ScopeManager()
    manager.create_root_scope("__main__")
    return manager


@pytest.fixture
def class_hierarchy_manager(scope_manager: ScopeManager) -> ScopeManager:
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
    scope_manager.enter_scope("Animal", ScopeType.CLASS)
    scope_manager.enter_scope("__init__", ScopeType.FUNCTION)
    scope_manager.define_symbol("self", SymbolType.PARAMETER)
    scope_manager.define_symbol("name", SymbolType.PARAMETER)
    scope_manager.exit_scope()  # __init__
    scope_manager.enter_scope("speak", ScopeType.FUNCTION)
    scope_manager.define_symbol("self", SymbolType.PARAMETER)
    scope_manager.exit_scope()  # speak
    scope_manager.enter_scope("wake_up", ScopeType.FUNCTION)
    scope_manager.define_symbol("self", SymbolType.PARAMETER)
    scope_manager.exit_scope()  # wake_up
    scope_manager.register_class([])
    scope_manager.exit_scope()  # Animal

    # Define Dog class inheriting from Animal
    scope_manager.enter_scope("Dog", ScopeType.CLASS)
    scope_manager.enter_scope("speak", ScopeType.FUNCTION)
    scope_manager.define_symbol("self", SymbolType.PARAMETER)
    scope_manager.exit_scope()  # speak
    scope_manager.enter_scope("bark", ScopeType.FUNCTION)
    scope_manager.define_symbol("self", SymbolType.PARAMETER)
    scope_manager.exit_scope()  # bark
    scope_manager.register_class(["__main__.Animal"])
    scope_manager.exit_scope()  # Dog

    # Finalize MROs
    scope_manager.calculate_all_mro()

    return scope_manager
