
from app.core.model.properties import CodePosition
import pytest

from app.core.services.code_element_service import CodeElementService
from app.core.model.nodes import ClassNode


@pytest.mark.asyncio
async def test_create_class(project_uow):
    class_service = CodeElementService(project_uow)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    class_node = ClassNode(
        id="class",
        name="Test Class",
        qname="test_project.test_class",
        description="This is a test class",
        code_position=position
    )
    new_class = await class_service.create(
        class_node
    )
    assert new_class is not None
    assert new_class.name == "Test Class"
    assert new_class.qname == "test_project.test_class"
    assert new_class.description == "This is a test class"


@pytest.mark.asyncio
async def test_get_class(project_uow, create_class, ):
    class_service = CodeElementService(project_uow)
    new_class = await class_service.get(create_class.id)
    assert new_class is not None
    assert new_class.name == "Test Class"
    assert new_class.qname == "test_project.test_class"
    assert new_class.description == "This is test class"


@pytest.mark.asyncio
async def test_update_class(project_uow, create_class):
    class_service = CodeElementService(project_uow)
    create_class.name = "Updated Class"
    create_class.description = "This is an updated class"
    new_class = await class_service.update(create_class)
    assert new_class is not None
    assert new_class.name == "Updated Class"
    assert new_class.description == "This is an updated class"


@pytest.mark.asyncio
async def test_delete_class(project_uow, create_class):
    class_service = CodeElementService(project_uow)
    # delete() expects a key, not a full id ("nodes/<key>")
    await class_service.delete(create_class.id)
    new_class = await class_service.get(create_class.id)
    assert new_class is None


@pytest.mark.asyncio
async def test_add_function_to_class(project_uow, create_class, create_function):
    class_service = CodeElementService(project_uow)
    await class_service.add_child(create_class.id, create_function.id, "function")
    functions = await class_service.get_children(create_class.id)
    assert len(functions) == 1

    assert functions[0].id == create_function.id


@pytest.mark.asyncio
async def test_add_class_to_class(project_uow, create_class, create_class2):
    class_service = CodeElementService(project_uow)
    await class_service.add_child(create_class.id, create_class2.id, "class")
    classes = await class_service.get_children(create_class.id)
    assert len(classes) == 1

    assert classes[0].id == create_class2.id


@pytest.mark.asyncio
async def test_add_call_to_class(project_uow, create_class, create_call):
    class_service = CodeElementService(project_uow)
    await class_service.add_child(create_class.id, create_call.id, "call")
    calls = await class_service.get_children(create_class.id)
    assert len(calls) == 1

    assert calls[0].id == create_call.id
