from app.core.services.project_service import ProjectService
from app.core.services.function_service import FunctionService
from app.core.services.call_service import CallService
from app.core.services.class_service import ClassService
from app.core.services.file_service import FileService
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.folder_service import FolderService
import pytest


@pytest.mark.asyncio
async def test_build_tree(
    create_project,
    create_function,
    create_class,
    create_call,
    create_repos,
    create_folder,
    create_file,
    create_call2,
):
    project_service = ProjectService(create_repos)
    function_service = FunctionService(create_repos)
    folder_service = FolderService(create_repos)
    file_service = FileService(create_repos)
    call_service = CallService(create_repos)
    class_service = ClassService(create_repos)

    await project_service.add_folder(
        create_project.id, create_folder.id)

    await folder_service.add_file(create_folder.id, create_file.id)

    # Build a strict tree (no node has multiple parents):
    # project -> folder -> file -> class -> function -> call -> call2
    await file_service.add_class(create_file.id, create_class.id)
    await class_service.add_function(create_class.id, create_function.id)
    await function_service.add_call(create_function.id, create_call.id)

    await call_service.add_call(create_call.id, create_call2.id)

    project_tree = await project_service.get_children(create_project.id)

    tree_builder = TreeBuilder(project_tree)
    tree = tree_builder.build()
    # print(project_tree)
    # Expect one root: the direct child of the project (the folder)
    assert isinstance(tree, list)

    # Since build() returns roots under the start project,
    # ensure folder present
    folder = tree[0]
    assert len(folder.children) == 1  # one file under folder
    file = folder.children[0]
    # Basic uniqueness per level
    assert len({child.id for child in folder.children}) == len(
        folder.children
    )

    # File should contain exactly one class
    assert len(file.children) == 1
    cls = file.children[0]
    assert len({child.id for child in file.children}) == len(
        file.children
    )

    # Class should contain exactly one function
    assert len(cls.children) == 1
    func = cls.children[0]
    assert len({child.id for child in cls.children}) == len(
        cls.children
    )

    # Function should contain exactly one call
    assert len(func.children) == 1
    call = func.children[0]
    assert len({child.id for child in func.children}) == len(
        func.children
    )

    # Call should contain exactly one call (call2)
    assert len(call.children) == 1
    # bind for readability; underscores ignore unused var lint
    _ = call.children[0]

    # Ensure no duplicates deep down
    assert len({child.id for child in call.children}) == len(
        call.children
    )
