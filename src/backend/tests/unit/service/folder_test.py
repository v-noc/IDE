from app.core.services.folder_service import FolderService


def test_create_folder(create_repos):
    folder_service = FolderService(create_repos)
    folder = folder_service.create(
        "Test Folder",
        "test_project.test_folder",
        "This is a test folder",
        "test_folder"
    )
    assert folder is not None
    assert folder.name == "Test Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is a test folder"


def test_get_folder(create_repos, create_folder):
    folder_service = FolderService(create_repos)
    folder = folder_service.get(create_folder.id)
    assert folder is not None
    assert folder.name == "Test Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is a test folder"


def test_update_folder(create_repos, create_folder):
    folder_service = FolderService(create_repos)
    create_folder.name = "Updated Folder"
    create_folder.description = "This is an updated folder"
    print(create_folder)
    folder = folder_service.update(create_folder)

    assert folder is not None
    assert folder.name == "Updated Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is an updated folder"


def test_add_folder_to_folder(create_repos, create_folder):
    folder_service = FolderService(create_repos)
    second_folder = folder_service.create(
        "second Folder",
        "test_project.test_folder.second_folder",
        "This is a new folder",
        "test_folder/second_folder"
    )
    folder_service.add_folder_to_folder(create_folder.id, second_folder.id)

    children_tree = folder_service.get_children(create_folder.id)

    assert len(children_tree) == 1
