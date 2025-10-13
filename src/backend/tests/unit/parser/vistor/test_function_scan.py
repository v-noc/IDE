from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import FunctionSchema


simple_func = """
def foo():
    pass
"""


def test_function_scan():
    result = scan(simple_func)
    assert len(result) == 1

    assert isinstance(result[0], FunctionSchema)
    print(result[0])


simple_func_with_param_return = """
def foo(x):
    return x
"""


def test_function_with_param_return():
    result = scan(simple_func_with_param_return)
    assert len(result) == 1

    schema = result[0]

    assert isinstance(schema, FunctionSchema)
    args = schema.args

    assert len(args) == 1
    assert args[0].name == "x"

    return_value = schema.return_values

    assert len(return_value) == 1
    assert return_value[0].name == "x"


nested_func = """

def foo():
    def tuna():
        pass

    def moon():
        pass
"""


def test_nested_func():
    result = scan(nested_func)

    assert len(result) == 1

    child_func = result[0].children
    assert len(child_func) == 2


func_with_defaults = """
def foo(a, b=2, c="hello"):
    pass
"""


def test_func_with_defaults():
    result = scan(func_with_defaults)
    assert len(result) == 1
    schema = result[0]
    assert isinstance(schema, FunctionSchema)
    args = schema.args
    assert len(args) == 3
    assert args[0].name == "a"
    assert args[1].name == "b"
    assert args[2].name == "c"


# func_with_args_kwargs = """
# def foo(*args, **kwargs):
#     pass
# """


# def test_func_with_args_kwargs():
#     result = scan(func_with_args_kwargs)
#     print(f"Result - {result}")
#     assert len(result) == 1
#     schema = result[0]
#     assert isinstance(schema, FunctionSchema)
#     args = schema.args
#     assert len(args) == 2
#     assert args[0].name == "args"
#     assert args[1].name == "kwargs"


func_with_position = """
def foo(): # line 2
    pass   # line 3
"""


def test_func_position():
    result = scan(func_with_position)
    assert len(result) == 1
    schema = result[0]
    assert isinstance(schema, FunctionSchema)
    assert schema.position.line_no == 2
    assert schema.position.end_line_no == 3


simple_func = """
def foo():
    \""" ID: 1 \"""
    pass
"""


def test_func_id():
    result = scan(simple_func)
    print(result)
    assert len(result) == 1
    schema = result[0]
    assert schema.id == "1"
