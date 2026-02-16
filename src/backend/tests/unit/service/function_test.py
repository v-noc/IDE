from app.core.services.function_service import FunctionService
from app.core.model.properties import CodePosition
import pytest


@pytest.mark.asyncio
async def test_create_function(create_repos, create_project):
    function_service = FunctionService(create_repos, create_project)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    function = await function_service.create(
        "function",
        "Test Function",
        "test_project.test_function",
        "This is a test function",
        position
    )
    assert function is not None
    assert function.name == "Test Function"
    assert function.qname == "test_project.test_function"
    assert function.description == "This is a test function"


@pytest.mark.asyncio
async def test_get_function(create_repos, create_function, create_project):
    function_service = FunctionService(create_repos, create_project)
    function = await function_service.get(create_function.id)
    assert function is not None
    assert function.name == "Test Function"
    assert function.qname == "test_project.test_function"
    assert function.description == "This is test function"


@pytest.mark.asyncio
async def test_update_function(create_repos, create_function, create_project):
    function_service = FunctionService(create_repos, create_project)
    create_function.name = "Updated Function"
    create_function.description = "This is an updated function"
    function = await function_service.update(create_function)
    assert function is not None
    assert function.name == "Updated Function"
    assert function.description == "This is an updated function"


@pytest.mark.asyncio
async def test_delete_function(create_repos, create_function, create_project):
    function_service = FunctionService(create_repos, create_project)
    # delete() expects a key, not a full id ("nodes/<key>")
    await function_service.delete(create_function.id)
    function = await function_service.get(create_function.id)
    assert function is None


@pytest.mark.asyncio
async def test_add_function_to_function(create_repos, create_function, create_function2, create_project):
    function_service = FunctionService(create_repos, create_project)
    await function_service.add_function(
        create_function.id, create_function2.id)
    functions = await function_service.get_children(create_function.id)
    assert len(functions) == 1

    assert functions[0].id == create_function2.id


@pytest.mark.asyncio
async def test_add_class_to_function(create_repos, create_function, create_class,  create_project):
    function_service = FunctionService(create_repos, create_project)
    await function_service.add_class(create_function.id, create_class.id)
    classes = await function_service.get_children(create_function.id)

    print(classes)
    assert len(classes) == 1

    assert classes[0].id == create_class.id


@pytest.mark.asyncio
async def test_add_call_to_function(create_repos, create_function, create_call, create_project):
    function_service = FunctionService(create_repos, create_project)
    await function_service.add_call(create_function.id, create_call.id)
    calls = await function_service.get_children(create_function.id)
    assert len(calls) == 1

    assert calls[0].id == create_call.id
