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
    animal_scope = Scope(
        name="Animal", scope_type=ScopeType.CLASS, code_position=code_position)
    manager.root_scope.add_child_scope(animal_scope)
    manager.enter_scope_by_scope(animal_scope)
    speak_scope = Scope(
        name="speak", scope_type=ScopeType.FUNCTION, code_position=code_position)
    animal_scope.add_child_scope(speak_scope)
    manager.enter_scope_by_scope(speak_scope)
    manager.define_symbol("self", SymbolType.PARAMETER,
                          code_position=code_position)
    manager.enter_scope_by_scope(animal_scope)
    manager.register_class([])  # Inherits from object implicitly

    # --- Define Dog ---
    manager.enter_scope_by_scope(manager.root_scope)
    dog_scope = Scope(name="Dog", scope_type=ScopeType.CLASS,
                      code_position=code_position)
    manager.root_scope.add_child_scope(dog_scope)
    manager.enter_scope_by_scope(dog_scope)
    dog_speak_scope = Scope(
        name="speak", scope_type=ScopeType.FUNCTION, code_position=code_position)
    dog_scope.add_child_scope(dog_speak_scope)
    manager.enter_scope_by_scope(dog_speak_scope)
    manager.define_symbol("self", SymbolType.PARAMETER,
                          code_position=code_position)
    manager.enter_scope_by_scope(dog_scope)
    manager.register_class(["__main__.Animal"])

    manager.calculate_all_mro()
    manager.enter_scope_by_scope(manager.root_scope)
    return manager
