from app.core.services.folder_service import FolderService
import pytest


@pytest.mark.asyncio
async def test_create_folder(create_repos):
    folder_service = FolderService(create_repos)
    folder = await folder_service.create(
        "Test Folder",
        "test_project.test_folder",
        "This is a test folder",
        "test_folder"
    )
    assert folder is not None
    assert folder.name == "Test Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is a test folder"


@pytest.mark.asyncio
async def test_get_folder(create_repos, create_folder):
    folder_service = FolderService(create_repos)
    folder = await folder_service.get(create_folder.id)
    assert folder is not None
    assert folder.name == "Test Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is a test folder"


@pytest.mark.asyncio
async def test_update_folder(create_repos, create_folder):
    folder_service = FolderService(create_repos)
    create_folder.name = "Updated Folder"
    create_folder.description = "This is an updated folder"

    folder = await folder_service.update(create_folder)

    assert folder is not None
    assert folder.name == "Updated Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is an updated folder"


@pytest.mark.asyncio
async def test_add_folder_to_folder(create_repos, create_folder):
    folder_service = FolderService(create_repos)
    second_folder = await folder_service.create(
        "second Folder",
        "test_project.test_folder.second_folder",
        "This is a new folder",
        "test_folder/second_folder"
    )
    await folder_service.add_folder(create_folder.id, second_folder.id)

    children_tree = await folder_service.get_children(create_folder.id)

    assert len(children_tree) == 1


@pytest.mark.asyncio
async def test_add_file_to_folder(create_repos, create_folder):
    folder_service = FolderService(create_repos)
    file = await folder_service.create(
        "Test File",
        "test_project.test_folder.test_file",
        "This is a test file",
        "test_folder/test_file"
    )

    children = await folder_service.get_children(create_folder.id)

    assert len(children) == 0
    await folder_service.add_file(create_folder.id, file.id)

    children = await folder_service.get_children(create_folder.id)

    assert len(children) == 1
