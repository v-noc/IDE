import pytest
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.core import Scope, ScopeType, SymbolType
from app.core.model.properties import CodePosition


@pytest.fixture
def populated_scope_manager(code_position):
    """
    Provides a ScopeManager instance populated with a class hierarchy:
    - class Animal:
        - def speak(self)
    - class Dog(Animal):
        - def speak(self)  # override
    """
    manager = ScopeManager()
    manager.create_root_scope("__main__")

    # --- Define Animal ---

    manager.enter_scope(name="Animal", scope_type=ScopeType.CLASS)

    manager.enter_scope(name="speak", scope_type=ScopeType.FUNCTION)

    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()
    manager.register_class([])  # Inherits from object implicitly
    manager.exit_scope()

    # --- Define Dog ---

    manager.enter_scope(name="Dog", scope_type=ScopeType.CLASS)

    manager.enter_scope("speak", ScopeType.FUNCTION)

    manager.define_symbol("self", SymbolType.PARAMETER)
    manager.exit_scope()
    manager.register_class(["__main__.Animal"])
    manager.exit_scope()

    manager.calculate_all_mro()
    manager.enter_scope_by_scope(manager.root_scope)
    return manager
