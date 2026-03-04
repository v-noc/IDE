from datetime import datetime, timezone
from re import S
from app.core.services.structure_service import StructureService
import pytest

from app.core.model.nodes import FolderNode
from app.core.model.schemas import FileSchema, FolderSchema


@pytest.mark.asyncio
async def test_create_folder(project_uow):
    folder_service = StructureService(project_uow)
    folder_node = FolderNode(
        id="folder",
        name="Test Folder",
        qname="test_project.test_folder",
        description="This is a test folder",
        path="test_folder"
    )
    folder = await folder_service.create(
        folder_node
    )

    assert folder is not None
    assert folder.name == "Test Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is a test folder"


@pytest.mark.asyncio
async def test_get_folder(project_uow, create_folder):
    folder_service = StructureService(project_uow)
    folder = await folder_service.get(create_folder.id)
    assert folder is not None
    assert folder.name == "Test Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is a test folder"


@pytest.mark.asyncio
async def test_update_folder(project_uow, create_folder):
    folder_service = StructureService(project_uow)
    create_folder.name = "Updated Folder"
    create_folder.description = "This is an updated folder"

    folder = await folder_service.update(create_folder)

    assert folder is not None
    assert folder.name == "Updated Folder"
    assert folder.qname == "test_project.test_folder"
    assert folder.description == "This is an updated folder"


@pytest.mark.asyncio
async def test_add_folder_to_folder(project_uow, create_folder, create_file):
    folder_service = StructureService(project_uow)
    second_folder_node = FolderNode(
        id="second_folder",
        name="Second Folder",
        qname="test_project.test_folder.second_folder",
        description="This is a new folder",
        path="test_folder/second_folder"
    )

    second_folder = await folder_service.create(
        second_folder_node
    )
    await folder_service.add_child(create_folder.id, second_folder.id, "folder")
    await folder_service.add_child(second_folder.id, create_file.id, "file")

    children_tree = await folder_service.get_children(create_folder.id, exclude_types=[FolderSchema.__name__])

    assert len(children_tree) == 1


@pytest.mark.asyncio
async def test_get_all_folders(project_uow, create_folder, create_file):
    folder_service = StructureService(project_uow)
    folders = await folder_service.get_all_folders()
    assert len(folders) == 1
    assert folders[0].name == "Test Folder"
    assert folders[0].qname == "test_project.test_folder"
    assert folders[0].description == "This is a test folder"


@pytest.mark.asyncio
async def test_batch_create_folders(project_uow):
    folder_service = StructureService(project_uow)
    await folder_service.create_batch([
        FolderNode(
            id="folder_1",
            name="Test Folder 1",
            qname="test_project.test_folder_1",
            description="This is a test folder",
            path="test_folder_1",

        ),
        FolderNode(
            id="folder_2",
            name="Test Folder 2",
            qname="test_project.test_folder_2",
            description="This is a test folder",
            path="test_folder_2"
        ),
    ])
    folders = await folder_service.get_all_folders()
    assert len(folders) == 2
    assert folders[0].name == "Test Folder 1"
    assert folders[0].qname == "test_project.test_folder_1"
    assert folders[0].description == "This is a test folder"
    assert folders[1].name == "Test Folder 2"
    assert folders[1].qname == "test_project.test_folder_2"
    assert folders[1].description == "This is a test folder"


@pytest.mark.asyncio
async def test_batch_update_folders(project_uow):
    folder_service = StructureService(project_uow)

    await folder_service.create_batch([
        FolderNode(
            id="folder_1",
            name="Test Folder 1",
            qname="test_project.test_folder_1",
            description="This is a test folder",
            path="test_folder_1",

        ),
        FolderNode(
            id="folder_2",
            name="Test Folder 2",
            qname="test_project.test_folder_2",
            description="This is a test folder",
            path="test_folder_2"
        ),
    ])

    folders = await folder_service.get_all_folders()
    folders[0].name = "Updated Folder 1"
    folders[0].description = "This is an updated folder"
    folders[1].name = "Updated Folder 2"
    folders[1].description = "This is an updated folder"
    await folder_service.update_batch(folders)
    folders = await folder_service.get_all_folders()
    assert len(folders) == 2
    assert folders[0].name == "Updated Folder 1"
    assert folders[0].qname == "test_project.test_folder_1"


@pytest.mark.asyncio
async def test_batch_move_folders(project_uow, create_folder, create_file):
    folder_service = StructureService(project_uow)

    await folder_service.create_batch([
        FolderNode(
            id="folder_1",
            name="Test Folder 1",
            qname="test_project.test_folder_1",
            description="This is a test folder",
            path="test_folder_1",

        ),
        FolderNode(
            id="folder_2",
            name="Test Folder 2",
            qname="test_project.test_folder_2",
            description="This is a test folder",
            path="test_folder_2"
        ),
    ])

    await folder_service.move_batch([(FolderSchema.__name__+"/folder_1", create_folder.id, "folder"), (f"{FolderSchema.__name__}/folder_2", FolderSchema.__name__+"/folder_1", "folder"), (create_file.id, FolderSchema.__name__+"/folder_1", "file")])

    children_tree = await folder_service.get_children(create_folder.id)
    assert len(children_tree) == 3

    for item in children_tree:
        if item.id == f"{FolderSchema.__name__}/folder_1":
            assert len(item.children) == 2
