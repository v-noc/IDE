from app.core.services import (
    ProjectService,
    GroupService,
    FileService,
    FolderService,
    ClassService,
    FunctionService,
    CallService,
)
from app.core.builder.tree_builder import TreeBuilder
from app.core.model.properties import CodePosition


def test_group_creation_files(create_repos):
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)

    project = project_service.create(
        "Test Project", "Test Project", "test_project")

    files1 = file_service.create(
        "Test File 1",
        "Test File 1",
        "test_file_1",
        "test_file_1.py",
        "test_file_1.py",
    )
    files2 = file_service.create(
        "Test File 2",
        "Test File 2",
        "test_file_2",
        "test_file_2.py",
        "test_file_2.py",
    )
    files3 = file_service.create(
        "Test File 3",
        "Test File 3",
        "test_file_3",
        "test_file_3.py",
        "test_file_3.py",
    )

    project_service.add_file(project.id, files1.id)
    project_service.add_file(project.id, files2.id)
    project_service.add_file(project.id, files3.id)

    children = project_service.get_children(project.id)

    tree = TreeBuilder(children).build()

    assert len(tree) == 3

    group = group_service.create(
        "Test Group", "Test Group", project.key, [files1.key, files2.key]
    )

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()

    assert len(tree) == 2

    group_children = None

    for child in tree:
        if child.node_type == "group":
            group_children = child
            break

    assert group_children is not None
    assert group_children.name == "Test Group"
    assert len(group_children.children) == 2

    group_children = group_service.get_children(group.id)
    assert len(group_children) == 2


def test_group_creation_folders(create_repos):
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    folder_service = FolderService(create_repos)

    project = project_service.create(
        "Test Project", "Test Project", "test_project")

    folder1 = folder_service.create(
        "Test Folder 1", "test_folder_1", "Test Folder 1", "folder_1"
    )
    folder2 = folder_service.create(
        "Test Folder 2", "test_folder_2", "Test Folder 2", "folder_2"
    )
    folder3 = folder_service.create(
        "Test Folder 3", "test_folder_3", "Test Folder 3", "folder_3"
    )

    project_service.add_folder(project.id, folder1.id)
    project_service.add_folder(project.id, folder2.id)
    project_service.add_folder(project.id, folder3.id)

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    assert len(tree) == 3

    group = group_service.create(
        "Test Group", "Test Group", project.key, [folder1.key, folder2.key]
    )

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    assert len(tree) == 2

    group_node = next((n for n in tree if n.node_type == "group"), None)
    assert group_node is not None
    assert group_node.name == "Test Group"
    assert len(group_node.children) == 2

    group_children = group_service.get_children(group.id)
    assert len(group_children) == 2


def test_group_creation_classes(create_repos):
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)
    class_service = ClassService(create_repos)

    project = project_service.create(
        "Test Project", "Test Project", "test_project")
    file_node = file_service.create(
        "Test File", "test_file", "Test File", "test_file.py", "test_file.py"
    )
    project_service.add_file(project.id, file_node.id)

    pos = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=2,
        end_col_offset=0,
    )
    cls1 = class_service.create("Class1", "Class1", "c1", pos)
    cls2 = class_service.create("Class2", "Class2", "c2", pos)
    cls3 = class_service.create("Class3", "Class3", "c3", pos)

    file_service.add_class(file_node.id, cls1.id)
    file_service.add_class(file_node.id, cls2.id)
    file_service.add_class(file_node.id, cls3.id)

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    file_in_tree = next((n for n in tree if n.node_type == "file"), None)
    assert file_in_tree is not None
    assert len(file_in_tree.children) == 3

    group = group_service.create(
        "Test Group", "Test Group", file_node.key, [cls1.key, cls2.key]
    )

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    file_in_tree = next((n for n in tree if n.node_type == "file"), None)
    assert file_in_tree is not None
    assert len(file_in_tree.children) == 2
    group_node = next(
        (
            n
            for n in file_in_tree.children
            if n.node_type == "group"
        ),
        None,
    )
    assert group_node is not None
    assert group_node.name == "Test Group"
    assert len(group_node.children) == 2

    group_children = group_service.get_children(group.id)
    assert len(group_children) == 2


def test_group_creation_functions(create_repos):
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)
    function_service = FunctionService(create_repos)

    project = project_service.create(
        "Test Project", "Test Project", "test_project")
    file_node = file_service.create(
        "Test File", "test_file", "Test File", "test_file.py", "test_file.py"
    )
    project_service.add_file(project.id, file_node.id)

    pos = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=2,
        end_col_offset=0,
    )
    fn1 = function_service.create("func1", "func1", "f1", pos)
    fn2 = function_service.create("func2", "func2", "f2", pos)
    fn3 = function_service.create("func3", "func3", "f3", pos)

    file_service.add_function(file_node.id, fn1.id)
    file_service.add_function(file_node.id, fn2.id)
    file_service.add_function(file_node.id, fn3.id)

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    file_in_tree = next((n for n in tree if n.node_type == "file"), None)
    assert file_in_tree is not None
    assert len(file_in_tree.children) == 3

    group = group_service.create(
        "Test Group", "Test Group", file_node.key, [fn1.key, fn2.key]
    )

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    file_in_tree = next((n for n in tree if n.node_type == "file"), None)
    assert file_in_tree is not None
    assert len(file_in_tree.children) == 2
    group_node = next(
        (
            n
            for n in file_in_tree.children
            if n.node_type == "group"
        ),
        None,
    )
    assert group_node is not None
    assert group_node.name == "Test Group"
    assert len(group_node.children) == 2

    group_children = group_service.get_children(group.id)
    assert len(group_children) == 2


def test_group_creation_calls(create_repos):
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)
    function_service = FunctionService(create_repos)
    call_service = CallService(create_repos)

    project = project_service.create(
        "Test Project", "Test Project", "test_project")
    file_node = file_service.create(
        "Test File", "test_file", "Test File", "test_file.py", "test_file.py"
    )
    project_service.add_file(project.id, file_node.id)

    pos = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=2,
        end_col_offset=0,
    )
    # Target function for calls
    target_fn = function_service.create("target", "target", "tf", pos)
    file_service.add_function(file_node.id, target_fn.id)

    c1 = call_service.create("call1", "call1", "c1", pos, target_fn.id)
    c2 = call_service.create("call2", "call2", "c2", pos, target_fn.id)
    c3 = call_service.create("call3", "call3", "c3", pos, target_fn.id)

    file_service.add_call(file_node.id, c1.id)
    file_service.add_call(file_node.id, c2.id)
    file_service.add_call(file_node.id, c3.id)

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    file_in_tree = next((n for n in tree if n.node_type == "file"), None)
    assert file_in_tree is not None
    assert len(file_in_tree.children) == 4  # target function + 3 calls

    group = group_service.create(
        "Test Group", "Test Group", file_node.key, [c1.key, c2.key]
    )

    children = project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    file_in_tree = next((n for n in tree if n.node_type == "file"), None)
    assert file_in_tree is not None
    # remaining: target function + group + one call
    assert len(file_in_tree.children) == 3
    group_node = next(
        (
            n
            for n in file_in_tree.children
            if n.node_type == "group"
        ),
        None,
    )
    assert group_node is not None
    assert group_node.name == "Test Group"
    assert len(group_node.children) == 2

    group_children = group_service.get_children(group.id)
    assert len(group_children) == 2
