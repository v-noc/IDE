from app.core.parser.scope_manager.core import SymbolType
from app.core.parser.scope_manager.manager import ScopeManager


def test_simple_instantiation_and_init(class_hierarchy_manager: ScopeManager):
    """
    Tests that instantiating a class correctly creates an instance symbol
    and implicitly calls its __init__ method.
    """
    manager = class_hierarchy_manager

    # Simulate: my_dog = Dog("Rex", "Golden Retriever")
    instance_symbol = manager.instantiate("Dog")
    init_method = manager.resolve_method("__main__.Dog", "__init__")

    assert init_method is not None

    manager.invoke(init_method, {"self": instance_symbol})
    manager.end_current_call()  # End __init__ call

    assert instance_symbol is not None
    assert instance_symbol.symbol_type == SymbolType.OBJECT_INSTANCE
    assert instance_symbol.instance_scope is not None
    assert instance_symbol.qualified_name == "__main__.Dog"

    call_graph = manager.get_call_graph()
    main_calls = call_graph.edges.get("__main__", [])
    assert len(main_calls) == 1
    init_call_site = main_calls[0]
    assert init_call_site.callee_symbol.qualified_name == "__main__.Animal.__init__"


def test_instance_method_call(class_hierarchy_manager: ScopeManager):
    """
    Tests calling a regular method on a class instance.
    """
    manager = class_hierarchy_manager
    instance_symbol = manager.instantiate("Dog")

    init_method = manager.resolve_method("__main__.Dog", "__init__")

    assert init_method is not None

    manager.invoke(init_method, {"self": instance_symbol})
    manager.end_current_call()  # End __init__ call

    # Simulate: my_dog.bark()
    bark_method = manager.resolve_method("__main__.Dog", "bark")
    assert bark_method is not None
    manager.invoke(bark_method, {"self": instance_symbol})
    manager.end_current_call()  # End bark()

    call_graph = manager.get_call_graph()
    main_calls = call_graph.edges.get("__main__", [])

    assert len(main_calls) == 2  # 1 for __init__, 1 for bark
    bark_call_site = main_calls[1]
    assert bark_call_site.callee_symbol.qualified_name == "__main__.Dog.bark"


def test_inherited_method_call(class_hierarchy_manager: ScopeManager):
    """
    Tests calling an inherited method, ensuring it's resolved up the MRO.
    """
    manager = class_hierarchy_manager
    instance_symbol = manager.instantiate("Dog")

    init_method = manager.resolve_method("__main__.Dog", "__init__")

    assert init_method is not None

    manager.invoke(init_method, {"self": instance_symbol})
    manager.end_current_call()  # End __init__ call

    # Simulate: my_dog.wake_up() -> should resolve to Animal.wake_up
    wake_up_method = manager.resolve_method("__main__.Dog", "wake_up")
    assert wake_up_method is not None
    assert wake_up_method.qualified_name == "__main__.Animal.wake_up"

    manager.invoke(wake_up_method, {"self": instance_symbol})
    manager.end_current_call()

    call_graph = manager.get_call_graph()
    main_calls = call_graph.edges.get("__main__", [])
    wake_up_call = main_calls[1]
    assert wake_up_call.callee_symbol.qualified_name == "__main__.Animal.wake_up"


def test_overridden_method_call(class_hierarchy_manager: ScopeManager):
    """
    Tests that calling an overridden method resolves to the subclass's version.
    """
    manager = class_hierarchy_manager
    instance_symbol = manager.instantiate("Dog")

    init_method = manager.resolve_method("__main__.Dog", "__init__")

    assert init_method is not None

    manager.invoke(init_method, {"self": instance_symbol})
    manager.end_current_call()  # End __init__ call

    # Simulate: my_dog.speak() -> should resolve to Dog.speak
    speak_method = manager.resolve_method("__main__.Dog", "speak")
    assert speak_method is not None
    assert speak_method.qualified_name == "__main__.Dog.speak"

    manager.invoke(speak_method, {"self": instance_symbol})
    manager.end_current_call()

    call_graph = manager.get_call_graph()
    main_calls = call_graph.edges.get("__main__", [])
    speak_call = main_calls[1]
    assert speak_call.callee_symbol.qualified_name == "__main__.Dog.speak"


def test_super_call_from_child(class_hierarchy_manager: ScopeManager):
    """
    Tests resolving a `super()` call from a child method to the parent method.
    """
    manager = class_hierarchy_manager
    instance_symbol = manager.instantiate("Dog")

    init_method = manager.resolve_method("__main__.Dog", "__init__")

    assert init_method is not None

    manager.invoke(init_method, {"self": instance_symbol})
    manager.end_current_call()  # End __init__ call

    # 1. Start the call to the child's overridden method
    dog_speak_method = manager.resolve_method("__main__.Dog", "speak")
    dog_speak_frame = manager.invoke(
        dog_speak_method, {"self": instance_symbol})

    dog_speak_scope = manager.get_scope_by_qname(
        dog_speak_method.qualified_name)

    # 2. Inside Dog.speak(), simulate a `super().speak()` call
    # We need the scope of Dog.speak to resolve `super` correctly.

    super_speak_method = manager.resolve_super_call(dog_speak_scope, "speak")

    assert super_speak_method is not None
    assert super_speak_method.qualified_name == "__main__.Animal.speak"

    # 3. Invoke the resolved super-method
    manager.invoke(super_speak_method, {"self": instance_symbol})
    manager.end_current_call()  # End super().speak()

    manager.end_current_call()  # End Dog.speak()

    # 4. Verify call graph
    call_graph = manager.get_call_graph()
    # Dog.speak was not called from __main__, but from the test logic.
    # The call graph tracks calls based on the current call frame.
    # The parent call is from Dog.speak
    dog_speak_qname = dog_speak_frame.callee_symbol.qualified_name
    dog_speak_calls = call_graph.edges.get(dog_speak_qname, [])
    assert len(dog_speak_calls) == 1
    super_call_site = dog_speak_calls[0]
    assert super_call_site.callee_symbol.qualified_name == "__main__.Animal.speak"


def test_self_call_within_method(class_hierarchy_manager: ScopeManager):
    """
    Tests a method calling another method on `self`.
    """
    manager = class_hierarchy_manager
    instance_symbol = manager.instantiate("Dog", {"name": "Rocky"})
    manager.end_current_call()

    # 1. Call a method, e.g., Dog.bark()
    bark_method = manager.resolve_method("__main__.Dog", "bark")
    bark_frame = manager.invoke(bark_method, {"self": instance_symbol})

    # 2. Inside bark(), simulate `self.wake_up()`
    wake_up_method = manager.resolve_method("__main__.Dog", "wake_up")
    assert wake_up_method.qualified_name == "__main__.Animal.wake_up"
    manager.invoke(wake_up_method, {"self": instance_symbol})
    manager.end_current_call()  # End self.wake_up()

    manager.end_current_call()  # End Dog.bark()

    # 3. Verify call graph
    call_graph = manager.get_call_graph()
    bark_qname = bark_frame.callee_symbol.qualified_name
    bark_calls = call_graph.edges.get(bark_qname, [])
    assert len(bark_calls) == 1
    wake_up_call = bark_calls[0]
    assert wake_up_call.callee_symbol.qualified_name == "__main__.Animal.wake_up"


def test_instance_variable_across_calls(class_hierarchy_manager: ScopeManager):
    """
    Tests that instance variables defined in __init__ persist and are
    accessible in other method calls.
    """
    manager = class_hierarchy_manager

    # 1. Instantiate, which calls __init__
    instance_symbol = manager.instantiate("Dog", {"name": "Daisy"})

    # 2. Inside __init__, define an instance variable: self.has_been_woken = False
    manager.define_symbol_on_instance(
        instance_symbol, "has_been_woken", SymbolType.VARIABLE, value=False)
    manager.end_current_call()  # End __init__

    # Check that the attribute exists on the instance scope
    assert "has_been_woken" in instance_symbol.instance_scope.symbols

    # 3. Call another method, e.g., wake_up()
    wake_up_method = manager.resolve_method("__main__.Dog", "wake_up")
    manager.invoke(wake_up_method, {"self": instance_symbol})

    # 4. Inside wake_up(), resolve and modify the instance variable
    woken_var = manager.resolve_symbol_on_instance(
        instance_symbol, "has_been_woken")
    assert woken_var is not None
    # Simulate modification
    woken_var.metadata["value"] = True

    manager.end_current_call()  # End wake_up()

    # 5. Verify the change back in the global context
    final_woken_var = instance_symbol.instance_scope.symbols["has_been_woken"]
    assert final_woken_var.metadata["value"] is True
