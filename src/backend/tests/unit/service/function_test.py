from app.core.services.function_service import FunctionService
from app.core.model.properties import CodePosition


def test_create_function(create_repos):
    function_service = FunctionService(create_repos)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    function = function_service.create(
        "Test Function",
        "test_project.test_function",
        "This is a test function",
        "test_function",
        position
    )
    assert function is not None
    assert function.name == "Test Function"
    assert function.qname == "test_project.test_function"
    assert function.description == "This is a test function"
