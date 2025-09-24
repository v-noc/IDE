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
        position
    )
    assert function is not None
    assert function.name == "Test Function"
    assert function.qname == "test_project.test_function"
    assert function.description == "This is a test function"


def test_get_function(create_repos, create_function):
    function_service = FunctionService(create_repos)
    function = function_service.get(create_function.id)
    assert function is not None
    assert function.name == "Test Function"
    assert function.qname == "test_project.test_function"
    assert function.description == "This is a test function"


def test_update_function(create_repos, create_function):
    function_service = FunctionService(create_repos)
    create_function.name = "Updated Function"
    create_function.description = "This is an updated function"
    function = function_service.update(create_function)
    assert function is not None
    assert function.name == "Updated Function"
    assert function.description == "This is an updated function"


def test_delete_function(create_repos, create_function):
    function_service = FunctionService(create_repos)
    function_service.delete(create_function.id)
    function = function_service.get(create_function.id)
    assert function is None


def test_add_function_to_function(create_repos, create_function, create_function2):
    function_service = FunctionService(create_repos)
    function_service.add_function_to_function(
        create_function.id, create_function2.id)
    functions = function_service.get_children(create_function.id)
    assert len(functions) == 1

    assert functions[0]['vertex']['_id'] == create_function2.id


def test_add_class_to_function(create_repos, create_function, create_class):
    function_service = FunctionService(create_repos)
    function_service.add_class_to_function(create_function.id, create_class.id)
    classes = function_service.get_children(create_function.id)
    assert len(classes) == 1

    assert classes[0]['vertex']['_id'] == create_class.id


def test_add_call_to_function(create_repos, create_function, create_call):
    function_service = FunctionService(create_repos)
    function_service.add_call_to_function(create_function.id, create_call.id)
    calls = function_service.get_children(create_function.id)
    assert len(calls) == 1

    assert calls[0]['vertex']['_id'] == create_call.id
