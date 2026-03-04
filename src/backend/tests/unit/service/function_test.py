from app.core.services.code_element_service import CodeElementService
from app.core.model.properties import CodePosition
import pytest

from app.core.model.nodes import FunctionNode


@pytest.mark.asyncio
async def test_create_function(project_uow):
    function_service = CodeElementService(project_uow)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    function_node = FunctionNode(
        id="FunctionSchema/function",
        name="Test Function",
        qname="test_project.test_function",
        description="This is a test function",
        code_position=position,
    )
    function = await function_service.create(
        function_node
    )
    assert function is not None
    assert function.id == "FunctionSchema/function"
    assert function.name == "Test Function"
    assert function.qname == "test_project.test_function"


@pytest.mark.asyncio
async def test_get_function(project_uow, create_function):
    function_service = CodeElementService(project_uow)
    function = await function_service.get(create_function.id)
    assert function is not None
    assert function.name == "Test Function"
    assert function.qname == "test_project.test_function"
    assert function.description == "This is test function"


@pytest.mark.asyncio
async def test_update_function(project_uow, create_function):
    function_service = CodeElementService(project_uow)
    create_function.name = "Updated Function"
    create_function.description = "This is an updated function"
    function = await function_service.update(create_function)
    assert function is not None
    assert function.name == "Updated Function"
    assert function.description == "This is an updated function"


@pytest.mark.asyncio
async def test_delete_function(project_uow, create_function):
    function_service = CodeElementService(project_uow)
    # delete() expects a key, not a full id ("nodes/<key>")
    await function_service.delete(create_function.id)
    function = await function_service.get(create_function.id)
    assert function is None


@pytest.mark.asyncio
async def test_add_function_to_function(project_uow, create_function, create_function2):
    function_service = CodeElementService(project_uow)
    await function_service.add_child(
        create_function.id, create_function2.id, "function")
    functions = await function_service.get_children(create_function.id)
    assert len(functions) == 1

    assert functions[0].id == create_function2.id


@pytest.mark.asyncio
async def test_add_class_to_function(project_uow, create_function, create_class):
    function_service = CodeElementService(project_uow)
    await function_service.add_child(create_function.id, create_class.id, "class")
    classes = await function_service.get_children(create_function.id)

    assert len(classes) == 1

    assert classes[0].id == create_class.id


@pytest.mark.asyncio
async def test_add_call_to_function(project_uow, create_function, create_call):
    function_service = CodeElementService(project_uow)
    await function_service.add_child(create_function.id, create_call.id, "call")
    calls = await function_service.get_children(create_function.id)
    assert len(calls) == 1

    assert calls[0].id == create_call.id
