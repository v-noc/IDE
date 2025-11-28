import os
from app.core.parser.ast.scanner import scan
from app.core.parser.ast.id_injector import inject_ids
from app.core.parser.ast.parser import JediParser


def test_id_injection():
    print("Testing ID Injection...")
    code_no_id = '''
class MyClass:
    """My Docstring"""
    def my_func(self):
        pass
'''
    # 1. Inject IDs
    new_code, modified = inject_ids(code_no_id)
    assert modified == True, "Should be modified"
    assert "ID:" in new_code, "ID should be injected"
    print("  [PASS] Injection on missing ID")

    # 2. Run again
    new_code_2, modified_2 = inject_ids(new_code)
    assert modified_2 == False, "Should NOT be modified on second run"
    assert new_code_2 == new_code, "Code should be identical"
    print("  [PASS] No modification on existing ID")


def test_parser_hierarchy():
    print("\nTesting Parser Hierarchy...")
    code = '''
class MyClass:
    """ID: 123"""
    def my_func(self):
        """ID: 456"""
        call_me()
        nested.call()

def outer_func():
    """ID: 789"""
    MyClass()
'''
    # We use scan but without file path to avoid writing
    nodes = scan(code)

    # Expected:
    # - ClassNode (MyClass)
    #   - FunctionNode (my_func)
    #     - CallNode (call_me)
    #     - CallNode (nested.call)
    # - FunctionNode (outer_func)
    #   - CallNode (MyClass)

    # Check MyClass
    my_class = next((n for n in nodes if n.name == "MyClass"), None)
    assert my_class is not None
    assert my_class.type == "class"
    assert my_class.id == "123"
    print("  [PASS] Class extraction")

    # Check my_func
    my_func = next((n for n in my_class.children if n.name == "my_func"), None)
    assert my_func is not None
    assert my_func.type == "function"
    assert my_func.id == "456"
    print("  [PASS] Method extraction")

    # Check calls in my_func
    calls = [n for n in my_func.children if n.type == "call"]
    assert len(calls) == 2
    assert any(c.name == "call_me" for c in calls)
    assert any(c.name == "nested.call" for c in calls)
    print("  [PASS] Call extraction inside method")

    # Check outer_func
    outer_func = next((n for n in nodes if n.name == "outer_func"), None)
    assert outer_func is not None
    assert outer_func.id == "789"

    # Check call in outer_func
    outer_calls = [n for n in outer_func.children if n.type == "call"]
    assert len(outer_calls) == 1
    assert outer_calls[0].name == "MyClass"
    print("  [PASS] Outer function and call extraction")


if __name__ == "__main__":
    try:
        test_id_injection()
        test_parser_hierarchy()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
