import pytest
from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import ClassNode, FunctionNode, CallNode


def test_hierarchy():
    code = """
class MyClass:
    def my_method(self):
        my_call()
"""
    nodes, _ = scan(code)

    # Check Class
    assert len(nodes) == 1
    cls = nodes[0]
    assert isinstance(cls, ClassNode)
    assert cls.name == "MyClass"

    # Check Method
    assert len(cls.children) == 1
    method = cls.children[0]
    assert isinstance(method, FunctionNode)
    assert method.name == "my_method"

    # Check Call
    assert len(method.children) == 1
    call = method.children[0]
    assert isinstance(call, CallNode)
    assert call.name == "my_call"


def test_naming():
    code = """
class ComplexName:
    pass

def my_func_123():
    pass

call.me.maybe()
"""
    nodes, _ = scan(code)
    print(nodes)
    cls = next(n for n in nodes if isinstance(n, ClassNode))
    assert cls.name == "ComplexName"

    func = next(n for n in nodes if isinstance(n, FunctionNode))
    assert func.name == "my_func_123"

    call = next(n for n in nodes if isinstance(n, CallNode))
    assert call.name == "call.me.maybe"


def test_call_detection_scenarios():
    code = """
def scenario_test():
    # 1. Statement
    simple_call()
    
    # 2. Assignment
    x = assigned_call()
    
    # 3. Arguments
    outer(inner_call())
    
    # 4. Nested
    chain.call().final()
    
    # 5. Data structures
    lst = [list_call()]
    dct = {'k': dict_call()}
"""
    nodes, _ = scan(code)
    func = nodes[0]
    calls = [n for n in func.children if isinstance(n, CallNode)]
    call_names = [c.name for c in calls]

    assert "simple_call" in call_names
    assert "assigned_call" in call_names
    assert "outer" in call_names
    assert "inner_call" in call_names

    assert "list_call" in call_names
    assert "dict_call" in call_names


def test_nested_definitions():
    code = """
def outer():
    def inner():
        inner_call()
    outer_call()
"""
    nodes, _ = scan(code)
    outer = nodes[0]

    # Inner function should be a child
    inner = next(n for n in outer.children if isinstance(n, FunctionNode))
    assert inner.name == "inner"

    # Inner call should be inside inner function
    inner_call = inner.children[0]
    assert inner_call.name == "inner_call"

    # Outer call should be inside outer function (sibling to inner def)
    outer_call = next(n for n in outer.children if isinstance(n, CallNode))
    assert outer_call.name == "outer_call"


def test_async_functions():
    code = """
async def async_func():
    pass
"""
    nodes, _ = scan(code)
    print(f" nodes {nodes}")
    async_func = nodes[0]

    assert async_func.name == "async_func"
    assert async_func.position.column == 0
