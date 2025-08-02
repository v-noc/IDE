from app.core.manager import CodeGraphManager

def test_create_virtual_folder():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")

    assert len(project.get_folders()) == 0

    folder = project.add_virtual_folder(folder_name="src")

    assert len(project.get_virtual_folders()) == 1
    assert len(folder.get_virtual_files()) == 0
    assert len(folder.get_virtual_folders()) == 0

def test_create_virtual_file():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")

    assert len(project.get_folders()) == 0

    folder = project.add_virtual_folder(folder_name="src")
    file = folder.add_virtual_file(file_name="test.py")


    assert len(folder.get_virtual_files()) == 1
    assert len(folder.get_virtual_folders()) == 0

def test_descendant_tree():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")

    assert len(project.get_folders()) == 0

    folder = project.add_virtual_folder(folder_name="src")
    folder2 = folder.add_virtual_folder(folder_name="test")
    file = folder2.add_virtual_file(file_name="test.py")

    assert len(project.get_virtual_folders()) == 1
    assert len(folder.get_virtual_files()) == 0
    assert len(folder.get_virtual_folders()) == 1
    assert len(folder2.get_virtual_files()) == 1
    assert len(folder2.get_virtual_folders()) == 0

    # print(folder.get_descendant_tree())

def test_get_virtual_files():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")

    assert len(project.get_virtual_folders()) == 0

    project.add_virtual_folder(folder_name="register")
    project.add_virtual_folder(folder_name="register/test")
    project.add_virtual_folder(folder_name="register/test/test")

    assert len(project.get_virtual_folders()) == 3


    