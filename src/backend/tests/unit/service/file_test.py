from app.core.services.file_service import FileService
from app.core.services.function_service import FunctionService


def test_create_file(create_repos):
    file_service = FileService(create_repos)
    file = file_service.create(
        "Test File",
        "test_project.test_file",
        "This is a test file",
        "test_file"
    )
    assert file is not None
    assert file.name == "Test File"
    assert file.qname == "test_project.test_file"
    assert file.description == "This is a test file"


def test_get_file(create_repos, create_file):
    file_service = FileService(create_repos)
    file = file_service.get(create_file.id)
    assert file is not None
    assert file.name == "Test File"
    assert file.qname == "test_project.test_file"
    assert file.description == "This is a test file"


def test_update_file(create_repos, create_file):
    file_service = FileService(create_repos)
    create_file.name = "Updated File"
    create_file.description = "This is an updated file"

    file = file_service.update(create_file)
    assert file is not None
    assert file.name == "Updated File"
    assert file.description == "This is an updated file"


def test_add_function_to_file(create_repos, create_file, create_function):
    file_service = FileService(create_repos)
    file_service.add_function_to_file(create_file.id, create_function.id)
    functions = file_service.get_children(create_file.id)
    assert len(functions) == 1

    assert functions[0]['vertex']['_id'] == create_function.id


def test_nested_functions(create_repos, create_file, create_function, create_function2):
    file_service = FileService(create_repos)
    function_service = FunctionService(create_repos)

    file_service.add_function_to_file(create_file.id, create_function.id)
    function_service.add_function_to_function(
        create_function.id, create_function2.id)

    functions = file_service.get_children(create_file.id)
    assert len(functions) == 2

    # assert functions[0]['vertex']['_id'] == create_function.id


def test_add_class_to_file(create_repos, create_file, create_class):
    file_service = FileService(create_repos)
    file_service.add_class_to_file(create_file.id, create_class.id)
    classes = file_service.get_children(create_file.id)
    assert len(classes) == 1

    assert classes[0]['vertex']['_id'] == create_class.id
