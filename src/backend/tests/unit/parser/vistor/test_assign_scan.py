from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import AssignSchema, NameSchema

simple_assign = """
a = 1
"""


def test_simple_assign():
    result = scan(simple_assign)
    assert len(result) == 1
    assign_schema = result[0]
    assert isinstance(assign_schema, AssignSchema)
    assert len(assign_schema.targets) == 1
    assert assign_schema.targets[0].name == "a"


assign_to_variable = """
a = b
"""


def test_assign_to_variable():
    result = scan(assign_to_variable)
    assert len(result) == 1
    assign_schema = result[0]
    assert isinstance(assign_schema, AssignSchema)
    assert len(assign_schema.targets) == 1
    assert assign_schema.targets[0].name == "a"
    assert len(assign_schema.value) == 1
    assert isinstance(assign_schema.value[0], NameSchema)
    assert assign_schema.value[0].name == "b"


multiple_assign = """
a = b = 1
"""


def test_multiple_assign():
    result = scan(multiple_assign)
    assert len(result) == 1
    assign_schema = result[0]
    assert isinstance(assign_schema, AssignSchema)
    assert len(assign_schema.targets) == 2
    assert assign_schema.targets[0].name == "b"
    assert assign_schema.targets[1].name == "a"


attribute_assign = """
a.b = 1
"""


def test_attribute_assign():
    result = scan(attribute_assign)
    assert len(result) == 1
    assign_schema = result[0]
    assert isinstance(assign_schema, AssignSchema)
    assert len(assign_schema.targets) == 1
    assert assign_schema.targets[0].name == "b"
    assert assign_schema.targets[0].value.name == "a"
