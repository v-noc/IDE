from app.core.services.file_service import FileService
from app.core.services.function_service import FunctionService
import pytest


@pytest.mark.asyncio
async def test_create_file(create_repos, create_project):
    file_service = FileService(create_repos, create_project)
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
async def test_get_file(create_repos, create_file, create_project):
    file_service = FileService(create_repos, create_project)
    file = await file_service.get(create_file.id)
    assert file is not None
    assert file.name == "Test File"
    assert file.qname == "test_project.test_file"
    assert file.description == "This is a test file"


@pytest.mark.asyncio
async def test_update_file(create_repos, create_file, create_project):
    file_service = FileService(create_repos, create_project)
    create_file.name = "Updated File"
    create_file.description = "This is an updated file"

    file = await file_service.update(create_file)
    assert file is not None
    assert file.name == "Updated File"
    assert file.description == "This is an updated file"


@pytest.mark.asyncio
async def test_add_function_to_file(create_repos, create_file, create_function):
    file_service = FileService(create_repos)
    await file_service.add_function(create_file.id, create_function.id)
    functions = await file_service.get_children(create_file.id)
    assert len(functions) == 1

    assert functions[0]['vertex']['_id'] == create_function.id


@pytest.mark.asyncio
async def test_nested_functions(create_repos, create_file, create_function, create_function2):
    file_service = FileService(create_repos)
    function_service = FunctionService(create_repos)

    await file_service.add_function(create_file.id, create_function.id)
    await function_service.add_function(
        create_function.id, create_function2.id)

    functions = await file_service.get_children(create_file.id)
    assert len(functions) == 2

    # assert functions[0]['vertex']['_id'] == create_function.id


@pytest.mark.asyncio
async def test_add_class_to_file(create_repos, create_file, create_class):
    file_service = FileService(create_repos)
    await file_service.add_class(create_file.id, create_class.id)
    classes = await file_service.get_children(create_file.id)
    assert len(classes) == 1

    assert classes[0]['vertex']['_id'] == create_class.id


@pytest.mark.asyncio
async def test_get_all_files(create_repos, create_file, create_folder, create_project):
    file_service = FileService(create_repos, create_project)
    files = await file_service.get_all_files()

    assert len(files) == 1
    assert files[0].name == "Test File"
    assert files[0].qname == "test_project.test_file"
    assert files[0].description == "This is a test file"
