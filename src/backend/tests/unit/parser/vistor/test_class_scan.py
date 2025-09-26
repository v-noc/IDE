from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import ClassSchema


simple_class = """
class Foo:
    pass
"""


def test_simple_class():
    result = scan(simple_class)

    assert len(result) == 1
    assert isinstance(result[0], ClassSchema)

    assert result[0].name == "Foo"


simple_class_with_method = """
class Foo:
    def __init__(self):
        pass
    def sleep(self):
        pass
"""


def test_simple_class_with_method():
    result = scan(simple_class_with_method)
    print(result)

    assert len(result) == 1
    foo_class = result[0]
    methods = foo_class.children

    assert isinstance(foo_class, ClassSchema)
    assert len(methods) == 2


simple_class_with_inheritance = """
class Bar:
    pass
class Foo(Bar):
    pass
"""


def test_simple_class_with_inheritance():
    result = scan(simple_class_with_inheritance)
    assert len(result) == 2
    foo_class = result[1]
    assert isinstance(foo_class, ClassSchema)
    assert foo_class.name == "Foo"
    assert len(foo_class.implements) == 1
    assert foo_class.implements[0].name == "Bar"


class_with_attributes = """
class Foo:
    a = 1
    b = "hello"
"""


def test_class_with_attributes():
    result = scan(class_with_attributes)
    assert len(result) == 1
    foo_class = result[0]
    assert isinstance(foo_class, ClassSchema)
    attributes = foo_class.children
    assert len(attributes) == 2
    assert attributes[0].targets[0].name == "a"
    assert attributes[1].targets[0].name == "b"


nested_class = """
class Foo:
    class Bar:
        pass
"""


def test_nested_class():
    result = scan(nested_class)
    assert len(result) == 1
    foo_class = result[0]
    assert isinstance(foo_class, ClassSchema)
    nested_classes = foo_class.children
    assert len(nested_classes) == 1
    assert isinstance(nested_classes[0], ClassSchema)
    assert nested_classes[0].name == "Bar"


class_with_position = """
class Foo: # line 2
    pass   # line 3
"""


def test_class_position():
    result = scan(class_with_position)
    assert len(result) == 1
    foo_class = result[0]
    assert isinstance(foo_class, ClassSchema)
    assert foo_class.position.line_no == 2
    assert foo_class.position.end_line_no == 3
