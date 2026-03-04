from app.core.services.file_service import FileService
from app.core.services.code_element_service import CodeElementService
import pytest

from app.core.model.nodes import FileNode


@pytest.mark.asyncio
async def test_create_file(project_uow):
    file_service = FileService(project_uow)
    file = await file_service.create(
        "file",
        "Test File",
        "test_project.test_file",
        "This is a test file",
        "test_file",
        hash="hash"
    )
    assert file is not None
    assert file.name == "Test File"
    assert file.qname == "test_project.test_file"
    assert file.description == "This is a test file"


@pytest.mark.asyncio
async def test_get_file(project_uow, create_file):
    file_service = FileService(project_uow)
    file = await file_service.get(create_file.id)
    assert file is not None
    assert file.name == "Test File"
    assert file.qname == "test_project.test_file"
    assert file.description == "This is a test file"


@pytest.mark.asyncio
async def test_update_file(project_uow, create_file):
    file_service = FileService(project_uow)
    create_file.name = "Updated File"
    create_file.description = "This is an updated file"

    file = await file_service.update(create_file)
    assert file is not None
    assert file.name == "Updated File"
    assert file.description == "This is an updated file"


@pytest.mark.asyncio
async def test_add_function_to_file(project_uow, create_file, create_function):
    file_service = FileService(project_uow)
    await file_service.add_function(create_file.id, create_function.id)
    functions = await file_service.get_children(create_file.id)
    assert len(functions) == 1

    assert functions[0].id == create_function.id


@pytest.mark.asyncio
async def test_nested_functions(project_uow, create_file, create_function, create_function2):
    file_service = FileService(project_uow)
    function_service = CodeElementService(project_uow)

    await file_service.add_function(create_file.id, create_function.id)
    await function_service.add_function(
        create_function.id, create_function2.id)

    functions = await file_service.get_children(create_file.id)
    assert len(functions) == 2

    # assert functions[0]['vertex']['_id'] == create_function.id


@pytest.mark.asyncio
async def test_add_class_to_file(project_uow, create_file, create_class):
    file_service = FileService(project_uow)
    await file_service.add_class(create_file.id, create_class.id)
    classes = await file_service.get_children(create_file.id)
    assert len(classes) == 1

    assert classes[0].id == create_class.id


@pytest.mark.asyncio
async def test_get_all_files(project_uow, create_file, create_folder):
    file_service = FileService(project_uow)
    files = await file_service.get_all_files()

    assert len(files) == 1
    assert files[0].name == "Test File"
    assert files[0].qname == "test_project.test_file"
    assert files[0].description == "This is a test file"


@pytest.mark.asyncio
async def test_batch_create_files(project_uow):
    file_service = FileService(project_uow)
    await file_service.create_batch([
        FileNode(
            id="file_1",
            name="Test File 1",
            qname="test_project.test_file_1",
            description="This is a test file",
            path="test_file_1",
            hash="hash"
        ),
        FileNode(
            id="file_2",
            name="Test File 2",
            qname="test_project.test_file_2",
            description="This is a test file",
            path="test_file_2",
            hash="hash"
        ),
    ])
    files = await file_service.get_all_files()
    assert len(files) == 2
    assert files[0].name == "Test File 1"


@pytest.mark.asyncio
async def test_batch_update_files(project_uow):
    file_service = FileService(project_uow)
    await file_service.create_batch([
        FileNode(
            id="file_1",
            name="Test File 1",
            qname="test_project.test_file_1",
            description="This is a test file",
            path="test_file_1",
            hash="hash"
        ),
        FileNode(
            id="file_2",
            name="Test File 2",
            qname="test_project.test_file_2",
            description="This is a test file",
            path="test_file_2",
            hash="hash"
        ),
    ])
    files = await file_service.get_all_files()
    files[0].name = "Updated File 1"
    files[0].description = "This is an updated file"
    files[1].name = "Updated File 2"
    files[1].description = "This is an updated file"
    await file_service.update_batch(files)
    files = await file_service.get_all_files()
    assert len(files) == 2
    assert files[0].name == "Updated File 1"
    assert files[0].description == "This is an updated file"
    assert files[1].name == "Updated File 2"
    assert files[1].description == "This is an updated file"


@pytest.mark.asyncio
async def test_batch_move_files(project_uow, create_file, create_function, create_class):
    file_service = FileService(project_uow)

    await file_service.move_batch([(create_function.id, create_file.id, "function"), (create_class.id, create_file.id, "class")])
    files = await file_service.get_children(create_file.id)

    assert len(files) == 2
    assert files[0].id == create_function.id
    assert files[1].id == create_class.id


@pytest.mark.asyncio
async def test_get_parent_file(project_uow, create_file, create_function, create_class):

    file_service = FileService(project_uow)

    await file_service.move_batch([(create_function.id, create_file.id, "function"), (create_class.id, create_function.id, "class")])
    parent_file = await file_service.get_parent_file(create_class.id)

    assert parent_file is not None
    assert parent_file.id == create_file.id
