from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import CallSchema, NameSchema, AttributeSchema

simple_call = """
foo()
"""


def test_simple_call():
    result = scan(simple_call)
    assert len(result) == 1
    call_schema = result[0]
    assert isinstance(call_schema, CallSchema)
    assert isinstance(call_schema.func, NameSchema)
    assert call_schema.func.name == "foo"


call_with_args = """
foo(a, b)
"""


def test_call_with_args():
    result = scan(call_with_args)
    assert len(result) == 1
    call_schema = result[0]
    assert isinstance(call_schema, CallSchema)
    assert len(call_schema.args) == 2
    assert call_schema.args[0].name == "a"
    assert call_schema.args[1].name == "b"


call_with_kwargs = """
foo(a=1, b="hello")
"""


def test_call_with_kwargs():
    result = scan(call_with_kwargs)
    assert len(result) == 1
    call_schema = result[0]
    assert isinstance(call_schema, CallSchema)
    assert len(call_schema.keywords) == 2
    assert call_schema.keywords[0].name == "a"
    assert call_schema.keywords[1].name == "b"


method_call = """
obj.foo()
"""


def test_method_call():
    result = scan(method_call)
    assert len(result) == 1
    call_schema = result[0]
    assert isinstance(call_schema, CallSchema)
    assert isinstance(call_schema.func, AttributeSchema)
    assert call_schema.func.name == "foo"
    assert call_schema.func.value.name == "obj"


chained_method_call = """
obj.foo().bar()
"""


def test_chained_method_call():
    result = scan(chained_method_call)
    assert len(result) == 1
    call_schema = result[0]
    assert isinstance(call_schema, CallSchema)
    assert isinstance(call_schema.func, AttributeSchema)
    assert call_schema.func.name == "bar"

    assert isinstance(call_schema.func.value, CallSchema)
    assert call_schema.func.value.func.name == "foo"
    assert call_schema.func.value.func.value.name == "obj"
