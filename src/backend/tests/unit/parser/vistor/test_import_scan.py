from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import ImportSchema, ImportFromSchema

simple_import = """
import os
"""


def test_simple_import():
    result = scan(simple_import)
    assert len(result) == 1
    import_schema = result[0]
    assert isinstance(import_schema, ImportSchema)
    assert len(import_schema.names) == 1
    assert import_schema.names[0].name == "os"


import_with_alias = """
import os as my_os
"""


def test_import_with_alias():
    result = scan(import_with_alias)
    assert len(result) == 1
    import_schema = result[0]
    assert isinstance(import_schema, ImportSchema)
    assert len(import_schema.names) == 1
    assert import_schema.names[0].name == "os"
    assert import_schema.names[0].asname == "my_os"


from_import = """
from os import path
"""


def test_from_import():
    result = scan(from_import)
    assert len(result) == 1
    import_schema = result[0]
    assert isinstance(import_schema, ImportFromSchema)
    assert import_schema.module_name == "os"
    assert len(import_schema.names) == 1
    assert import_schema.names[0].name == "path"


from_import_with_alias = """
from os import path as my_path
"""


def test_from_import_with_alias():
    result = scan(from_import_with_alias)
    assert len(result) == 1
    import_schema = result[0]
    assert isinstance(import_schema, ImportFromSchema)
    assert import_schema.module_name == "os"
    assert len(import_schema.names) == 1
    assert import_schema.names[0].name == "path"
    assert import_schema.names[0].asname == "my_path"


relative_import = """
from . import utils
"""


def test_relative_import():
    result = scan(relative_import)
    assert len(result) == 1
    import_schema = result[0]
    assert isinstance(import_schema, ImportFromSchema)
    assert import_schema.level == 1
    assert import_schema.module_name is None
    assert len(import_schema.names) == 1
    assert import_schema.names[0].name == "utils"
