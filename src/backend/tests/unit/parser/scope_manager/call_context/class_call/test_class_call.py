from app.core.parser.scope_manager.storage.models import SymbolType
from app.core.parser.scope_manager.manger import ScopeManager


def test_simple_instantiation_and_init(class_hierarchy_manager: ScopeManager):
    """
    Tests that instantiating a class correctly creates an instance symbol
    and implicitly calls its __init__ method.
    """
    manager = class_hierarchy_manager

    dog_class = manager.repo.symbols.get_by_name_in_scope(
        "Dog", manager.root_scope_id)

    # Simulate: my_dog = Dog("Rex", "Golden Retriever")
    instance_symbol_id = manager.instantiation_service.instantiate_class(
        dog_class.id, manager.current_scope_id)
    class_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        dog_class.id)
    init_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "__init__")

    assert init_method is not None

    frame_id = manager.call_tracking_service.start_call(
        init_method.id, {"self": instance_symbol_id}, manager.current_scope_id)
    manager.call_tracking_service.end_call(
        frame_id, return_symbol_id=None)

    instance_symbol = manager.repo.symbols.get_by_id(instance_symbol_id)

    assert instance_symbol_id is not None
    assert instance_symbol.symbol_type == SymbolType.OBJECT_INSTANCE
    assert instance_symbol.instance_scope_id is not None
    assert instance_symbol.original_symbol_id == dog_class.id

    # Verify the call graph records the __init__ call from the root scope
    call_sites = manager.resolver.call_graph_resolver.get_root_call_from_scope(
        manager.root_scope_id
    )
    assert len(call_sites) == 1
    init_call_site = call_sites[0]
    init_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        init_call_site.callee_frame.callee_symbol.id
    )
    assert init_qname == "__main__.Animal.__init__"


def test_instance_method_call(class_hierarchy_manager: ScopeManager):
    """
    Tests calling a regular method on a class instance.
    """
    manager = class_hierarchy_manager
    dog_class = manager.repo.symbols.get_by_name_in_scope(
        "Dog", manager.root_scope_id)
    instance_symbol_id = manager.instantiation_service.instantiate_class(
        dog_class.id, manager.current_scope_id)
    class_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        dog_class.id)

    init_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "__init__")

    assert init_method is not None

    frame_id = manager.call_tracking_service.start_call(
        init_method.id, {"self": instance_symbol_id}, manager.current_scope_id)
    manager.call_tracking_service.end_call(
        frame_id, return_symbol_id=None)

    # Simulate: my_dog.bark()
    bark_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "bark")
    assert bark_method is not None
    frame_id = manager.call_tracking_service.start_call(
        bark_method.id, {"self": instance_symbol_id}, manager.current_scope_id)
    manager.call_tracking_service.end_call(
        frame_id, return_symbol_id=None)

    # Verify that both __init__ and bark were recorded from the root scope
    call_sites = manager.resolver.call_graph_resolver.get_root_call_from_scope(
        manager.root_scope_id
    )
    assert len(call_sites) == 2  # 1 for __init__, 1 for bark
    bark_call_site = call_sites[1]
    bark_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        bark_call_site.callee_frame.callee_symbol.id
    )
    assert bark_qname == "__main__.Dog.bark"


def test_inherited_method_call(class_hierarchy_manager: ScopeManager):
    """
    Tests calling an inherited method, ensuring it's resolved up the MRO.
    """
    manager = class_hierarchy_manager
    dog_class = manager.repo.symbols.get_by_name_in_scope(
        "Dog", manager.root_scope_id)
    instance_symbol_id = manager.instantiation_service.instantiate_class(
        dog_class.id, manager.current_scope_id)
    class_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        dog_class.id)
    init_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "__init__")

    assert init_method is not None

    frame_id = manager.call_tracking_service.start_call(
        init_method.id, {"self": instance_symbol_id}, manager.current_scope_id)
    manager.call_tracking_service.end_call(
        frame_id, return_symbol_id=None)

    # Simulate: my_dog.wake_up() -> should resolve to Animal.wake_up
    wake_up_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "wake_up")
    assert wake_up_method is not None
    frame_id = manager.call_tracking_service.start_call(
        wake_up_method.id, {"self": instance_symbol_id}, manager.current_scope_id)
    manager.call_tracking_service.end_call(
        frame_id, return_symbol_id=None)

    # Verify that both __init__ and wake_up were recorded from the root scope
    call_sites = manager.resolver.call_graph_resolver.get_root_call_from_scope(
        manager.root_scope_id
    )
    assert len(call_sites) == 2  # 1 for __init__, 1 for wake_up
    wake_up_call_site = call_sites[1]
    wake_up_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        wake_up_call_site.callee_frame.callee_symbol.id
    )
    assert wake_up_qname == "__main__.Animal.wake_up"


def test_overridden_method_call(class_hierarchy_manager: ScopeManager):
    """
    Tests that calling an overridden method resolves to the subclass's version.
    """
    manager = class_hierarchy_manager
    dog_class = manager.repo.symbols.get_by_name_in_scope(
        "Dog", manager.root_scope_id
    )
    instance_symbol_id = manager.instantiation_service.instantiate_class(
        dog_class.id, manager.current_scope_id
    )
    class_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        dog_class.id
    )

    # Call Dog.__init__(self)
    init_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "__init__"
    )
    assert init_method is not None

    init_frame_id = manager.call_tracking_service.start_call(
        init_method.id, {"self": instance_symbol_id}, manager.current_scope_id
    )
    manager.call_tracking_service.end_call(
        init_frame_id, return_symbol_id=None)

    # Simulate: my_dog.speak() -> should resolve to Dog.speak
    speak_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "speak"
    )
    assert speak_method is not None

    speak_frame_id = manager.call_tracking_service.start_call(
        speak_method.id, {"self": instance_symbol_id}, manager.current_scope_id
    )
    manager.call_tracking_service.end_call(
        speak_frame_id, return_symbol_id=None)

    # Verify that both __init__ and speak were recorded from the root scope
    call_sites = manager.resolver.call_graph_resolver.get_root_call_from_scope(
        manager.root_scope_id
    )
    assert len(call_sites) == 2  # 1 for __init__, 1 for speak
    speak_call_site = call_sites[1]
    speak_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        speak_call_site.callee_frame.callee_symbol.id
    )
    assert speak_qname == "__main__.Dog.speak"


def test_super_call_from_child(class_hierarchy_manager: ScopeManager):
    """
    Tests resolving a `super()` call from a child method to the parent method.
    """
    manager = class_hierarchy_manager
    dog_class = manager.repo.symbols.get_by_name_in_scope(
        "Dog", manager.root_scope_id
    )
    instance_symbol_id = manager.instantiation_service.instantiate_class(
        dog_class.id, manager.current_scope_id
    )
    class_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        dog_class.id
    )

    # 1. Call Dog.__init__(self)
    init_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "__init__"
    )
    assert init_method is not None

    init_frame_id = manager.call_tracking_service.start_call(
        init_method.id, {"self": instance_symbol_id}, manager.current_scope_id
    )
    manager.call_tracking_service.end_call(
        init_frame_id, return_symbol_id=None)

    # 2. Start the call to the child's overridden method Dog.speak(self)
    dog_speak_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "speak"
    )
    assert dog_speak_method is not None

    dog_speak_frame_id = manager.call_tracking_service.start_call(
        dog_speak_method.id,
        {"self": instance_symbol_id},
        manager.current_scope_id,
    )
    dog_speak_frame = manager.repo.call_frames.get_by_id(dog_speak_frame_id)

    # 3. Inside Dog.speak(), simulate a `super().speak()` call using the MRO
    super_speak_method = manager.resolver.inheritance_resolver.method_resolver.resolve_super_call(
        class_qname, "speak"
    )
    assert super_speak_method is not None

    super_speak_frame_id = manager.call_tracking_service.start_call(
        super_speak_method.id,
        {"self": instance_symbol_id},
        dog_speak_frame.execution_scope_id,
    )
    manager.call_tracking_service.end_call(
        super_speak_frame_id, return_symbol_id=None
    )

    # End Dog.speak()
    manager.call_tracking_service.end_call(
        dog_speak_frame_id, return_symbol_id=None
    )

    # 4. Verify call graph: Dog.speak's execution scope should have a call to Animal.speak
    dog_speak_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        dog_speak_method.id
    )
    call_tree = manager.resolver.call_graph_resolver.get_call_tree(
        dog_speak_frame.execution_scope_id
    )
    # The root of this tree is the super().speak() call
    assert len(call_tree) == 1
    super_call = call_tree[0]
    super_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        super_call['callee_symbol'].id
    )
    assert super_qname == "__main__.Animal.speak"


def test_self_call_within_method(class_hierarchy_manager: ScopeManager):
    """
    Tests a method calling another method on `self`.
    """
    manager = class_hierarchy_manager
    dog_class = manager.repo.symbols.get_by_name_in_scope(
        "Dog", manager.root_scope_id
    )
    instance_symbol_id = manager.instantiation_service.instantiate_class(
        dog_class.id, manager.current_scope_id
    )
    class_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        dog_class.id
    )

    # Call Dog.__init__(self)
    init_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "__init__"
    )
    assert init_method is not None

    init_frame_id = manager.call_tracking_service.start_call(
        init_method.id, {"self": instance_symbol_id}, manager.current_scope_id
    )
    manager.call_tracking_service.end_call(
        init_frame_id, return_symbol_id=None)

    # 1. Call a method, e.g., Dog.bark()
    bark_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "bark"
    )
    assert bark_method is not None

    bark_frame_id = manager.call_tracking_service.start_call(
        bark_method.id, {"self": instance_symbol_id}, manager.current_scope_id
    )
    bark_frame = manager.repo.call_frames.get_by_id(bark_frame_id)

    # 2. Inside bark(), simulate `self.wake_up()`
    wake_up_method = manager.resolver.inheritance_resolver.method_resolver.resolve_method(
        class_qname, "wake_up"
    )
    assert wake_up_method is not None
    wake_up_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        wake_up_method.id
    )
    assert wake_up_qname == "__main__.Animal.wake_up"

    wake_up_frame_id = manager.call_tracking_service.start_call(
        wake_up_method.id,
        {"self": instance_symbol_id},
        bark_frame.execution_scope_id,
    )
    manager.call_tracking_service.end_call(
        wake_up_frame_id, return_symbol_id=None
    )

    # End Dog.bark()
    manager.call_tracking_service.end_call(
        bark_frame_id, return_symbol_id=None
    )

    # 3. Verify call graph: Dog.bark's execution scope should have a call
    # to Animal.wake_up
    call_tree = manager.resolver.call_graph_resolver.get_call_tree(
        bark_frame.execution_scope_id
    )
    assert len(call_tree) == 1
    wake_call = call_tree[0]
    wake_called_qname = manager.resolver.qname_resolver.get_qname_for_symbol(
        wake_call['callee_symbol'].id
    )
    assert wake_called_qname == "__main__.Animal.wake_up"
