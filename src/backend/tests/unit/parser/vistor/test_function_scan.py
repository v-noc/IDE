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
