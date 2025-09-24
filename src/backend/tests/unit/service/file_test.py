from app.core.services.file_service import FileService


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
