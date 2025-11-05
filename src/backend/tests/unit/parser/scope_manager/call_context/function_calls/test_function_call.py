from app.core.parser.scope_manager.core import ScopeType, SymbolType
from app.core.parser.scope_manager.manager import ScopeManager


def test_simple_function_call(scope_manager: ScopeManager):
    """
    Tests a simple function declaration and call, then verifies the call graph.
    """
    # 1. Define a simple function `greet` in the global scope
    # def greet(name): ...
    scope_manager.enter_scope("greet", ScopeType.FUNCTION)
    scope_manager.define_symbol("name", SymbolType.PARAMETER)
    scope_manager.exit_scope()

    # 2. Invoke the function from the global scope
    scope_manager.invoke("greet", {"name": "World"})
    scope_manager.end_current_call()

    # 3. Assert the call graph structure
    call_graph = scope_manager.get_call_graph()
    assert len(call_graph.edges) == 1

    # The caller should be the main module
    caller_qname = "__main__"
    assert caller_qname in call_graph.edges

    # It should have one call site
    call_sites = call_graph.edges[caller_qname]
    assert len(call_sites) == 1

    # The call site should point to the 'greet' function
    call_site = call_sites[0]
    assert call_site.callee_symbol.qualified_name == "__main__.greet"


def test_closure_creation_and_invocation(scope_manager: ScopeManager):
    """
    Tests creating a closure, invoking it, and ensuring it can access its
    captured environment.
    """
    # 1. Define a factory function with a nested function
    # def factory(msg):
    #   def closure():
    #     ...
    #   return closure
    factory_scope = scope_manager.enter_scope("factory", ScopeType.FUNCTION)
    scope_manager.define_symbol("msg", SymbolType.PARAMETER)
    scope_manager.enter_scope("closure", ScopeType.FUNCTION)
    scope_manager.exit_scope()  # Exit closure scope
    scope_manager.exit_scope()  # Exit factory scope

    # Get the symbol for the nested function
    closure_symbol = factory_scope.symbols["closure"]

    # 2. Call the factory to create a closure instance
    scope_manager.invoke("factory", {"msg": "Hello Closure"})
    closure_instance = scope_manager.end_current_call(
        return_value=closure_symbol)

    # Assert that a closure symbol with a captured frame was returned
    assert closure_instance is not None
    assert closure_instance.name == "closure"
    assert closure_instance.captured_frame is not None, (
        "Closure should have a captured frame"
    )

    # 3. Invoke the returned closure
    scope_manager.invoke(closure_instance, {})

    # 4. From within the closure's execution context, resolve a captured variable
    resolved_msg_symbol = scope_manager.resolve_symbol_in_context("msg")
    assert resolved_msg_symbol is not None
    assert resolved_msg_symbol.name == "msg"

    scope_manager.end_current_call()  # End closure call

    # 5. Verify the call graph
    call_graph = scope_manager.get_call_graph()
    main_calls = call_graph.edges.get("__main__", [])
    assert len(main_calls) == 2
    assert main_calls[0].callee_symbol.qualified_name == "__main__.factory"
    assert main_calls[1].callee_symbol.qualified_name == "__main__.factory.closure"


def test_independent_closures(scope_manager: ScopeManager):
    """
    Tests that calling a factory function twice creates two independent closures
    with their own captured environments.
    """
    # 1. Define the factory function (same as before)
    factory_scope = scope_manager.enter_scope("factory", ScopeType.FUNCTION)
    scope_manager.define_symbol("msg", SymbolType.PARAMETER)
    scope_manager.enter_scope("closure", ScopeType.FUNCTION)
    scope_manager.exit_scope()
    scope_manager.exit_scope()
    closure_symbol = factory_scope.symbols["closure"]

    # 2. Create the first closure
    scope_manager.invoke("factory", {"msg": "First Message"})
    closure_one = scope_manager.end_current_call(return_value=closure_symbol)
    closure_one_id = closure_one.captured_frame.id

    # 3. Create the second closure
    scope_manager.invoke("factory", {"msg": "Second Message"})
    closure_two = scope_manager.end_current_call(return_value=closure_symbol)
    closure_two_id = closure_two.captured_frame.id
    print("Closure 2", closure_two_id)

    # # 4. Assert that the closures are distinct and have different captured frames
    assert closure_one is not None and closure_two is not None

    assert closure_one_id != closure_two_id

    # # 5. Invoke the first closure and check its context

    # scope_manager.invoke(closure_one, {})
    # resolved_msg1 = scope_manager.resolve_symbol_in_context("msg")
    # assert resolved_msg1.defining_scope.parent.id == closure_one.captured_frame.id
    # scope_manager.end_current_call()

    # # 6. Invoke the second closure and check its context
    # scope_manager.invoke(closure_two, {})
    # resolved_msg2 = scope_manager.resolve_symbol_in_context("msg")
    # assert resolved_msg2.defining_scope.parent.id == closure_two.captured_frame.id
    # scope_manager.end_current_call()


def test_nested_function_call(scope_manager: ScopeManager):
    """
    Tests a function that defines and then immediately calls a nested function,
    verifying the call relationship in the graph.
    """
    # 1. Define an outer function with a nested function
    # def outer():
    #   def inner(): ...
    #   inner()
    scope_manager.enter_scope("outer", ScopeType.FUNCTION)
    scope_manager.enter_scope("inner", ScopeType.FUNCTION)
    scope_manager.exit_scope()  # Exit inner scope
    scope_manager.exit_scope()  # Exit outer scope

    # 2. Simulate the execution flow: call outer()
    outer_frame = scope_manager.invoke("outer", {})

    # 3. From within outer's context, look up and call inner()
    inner_symbol = scope_manager.resolve_symbol_in_context("inner")
    assert inner_symbol is not None, "Could not find 'inner' from within 'outer'"
    scope_manager.invoke(inner_symbol, {})
    scope_manager.end_current_call()  # End inner call

    scope_manager.end_current_call()  # End outer call

    # 4. Verify the call graph
    call_graph = scope_manager.get_call_graph()
    # __main__ should call outer
    main_calls = call_graph.edges.get("__main__", [])
    assert len(main_calls) == 1
    assert main_calls[0].callee_symbol.qualified_name == "__main__.outer"

    # outer's execution scope should call inner
    outer_exec_qname = outer_frame.callee_symbol.qualified_name
    outer_calls = call_graph.edges.get(outer_exec_qname, [])
    assert len(outer_calls) == 1
    assert outer_calls[0].callee_symbol.qualified_name == "__main__.outer.inner"


def test_callback_function(scope_manager: ScopeManager):
    """
    Tests passing a function as a callback and invoking it, checking the call graph.
    """
    # 1. Define the function that will be used as a callback
    # def my_callback(data): ...
    scope_manager.enter_scope("my_callback", ScopeType.FUNCTION)
    scope_manager.define_symbol("data", SymbolType.PARAMETER)
    scope_manager.exit_scope()

    # 2. Define the function that accepts and calls the callback
    # def invoker(callback_func):
    #   callback_func("some_data")
    scope_manager.enter_scope("invoker", ScopeType.FUNCTION)
    scope_manager.define_symbol("callback_func", SymbolType.PARAMETER)
    scope_manager.exit_scope()

    # 3. Get the symbol for the callback function
    callback_symbol = scope_manager.lookup_symbol("my_callback")
    assert callback_symbol is not None

    # 4. Simulate the call to the invoker, passing the callback symbol as an argument
    invoker_frame = scope_manager.invoke(
        "invoker", {"callback_func": callback_symbol})

    # 5. From within the invoker's context, resolve and call the callback
    callback_param_symbol = scope_manager.resolve_symbol_in_context(
        "callback_func")
    assert callback_param_symbol is not None
    # The parameter symbol should point to the actual callback function symbol
    final_callee = callback_param_symbol.resolve_final()
    assert final_callee.qualified_name == "__main__.my_callback"

    scope_manager.invoke(final_callee, {"data": "some_data"})
    scope_manager.end_current_call()  # End callback call

    scope_manager.end_current_call()  # End invoker call

    # 6. Verify the call graph
    call_graph = scope_manager.get_call_graph()
    # __main__ -> invoker
    main_calls = call_graph.edges.get("__main__", [])
    assert len(main_calls) == 1
    assert main_calls[0].callee_symbol.qualified_name == "__main__.invoker"

    # invoker -> my_callback
    invoker_exec_qname = invoker_frame.callee_symbol.qualified_name
    call_graph = scope_manager.get_call_graph()

    invoker_calls = call_graph.edges.get(invoker_exec_qname, [])
    assert len(invoker_calls) == 1

    assert invoker_calls[0].callee_symbol.qualified_name == "__main__.my_callback"


def test_closure_calling_another_function(scope_manager: ScopeManager):
    """
    Tests that a call from within a closure is correctly recorded in the call graph.
    """
    # 1. Define a target function to be called by the closure
    scope_manager.enter_scope("target_func", ScopeType.FUNCTION)
    scope_manager.exit_scope()

    # 2. Define a factory that creates a closure
    factory_scope = scope_manager.enter_scope("factory", ScopeType.FUNCTION)
    scope_manager.enter_scope("closure", ScopeType.FUNCTION)
    scope_manager.exit_scope()  # Exit closure scope
    scope_manager.exit_scope()  # Exit factory scope
    closure_symbol = factory_scope.symbols["closure"]

    # 3. Create the closure instance
    scope_manager.invoke("factory", {})
    closure_instance = scope_manager.end_current_call(
        return_value=closure_symbol)

    # 4. Invoke the closure
    closure_frame = scope_manager.invoke(closure_instance, {})

    # 5. From within the closure's context, call the target function
    target_symbol = scope_manager.lookup_symbol("target_func")
    assert target_symbol is not None
    scope_manager.invoke(target_symbol, {})
    scope_manager.end_current_call()  # End target_func call

    scope_manager.end_current_call()  # End closure call

    # 6. Verify the call graph
    call_graph = scope_manager.get_call_graph()

    # Check calls made from the global scope (__main__)
    main_calls = call_graph.edges.get("__main__", [])
    assert len(main_calls) == 2
    assert main_calls[0].callee_symbol.qualified_name == "__main__.factory"
    assert main_calls[1].callee_symbol.qualified_name == "__main__.factory.closure"

    # Check calls made from the closure's execution scope
    closure_exec_qname = closure_frame.callee_symbol.qualified_name
    closure_calls = call_graph.edges.get(closure_exec_qname, [])
    assert len(closure_calls) == 1
    assert closure_calls[0].callee_symbol.qualified_name == "__main__.target_func"
