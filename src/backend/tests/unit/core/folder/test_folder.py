from app.core.manager import CodeGraphManager


def test_create_folder():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")

    assert len(project.get_folders()) == 0

    folder = project.add_folder(folder_name="src", folder_path=project.path + "/")

    assert len(project.get_folders()) == 1
    assert folder.get_files() == []
    assert folder.get_folders() == []

def test_create_folder_in_folder():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")

    assert len(project.get_folders()) == 0

    folder = project.add_folder(folder_name="src", folder_path=project.absolute_path + "/")
    folder.add_folder(folder_name="core", folder_path=folder.absolute_path+"/")
    folder.add_folder(folder_name="api", folder_path=folder.absolute_path+"/")

    assert len(project.get_folders()) == 1
    assert len(folder.get_folders()) == 2
    assert len(folder.get_files()) == 0

    assert folder.get_folders()[1].name == "core"
    assert folder.get_folders()[0].name == "api"

    assert folder.get_folders()[1].absolute_path == folder.absolute_path+"/core"
    assert folder.get_folders()[0].absolute_path == folder.absolute_path+"/api"

def test_multi_level_nested_folder(create_folder):
    folder = create_folder

    api_folder = folder.add_folder(folder_name="api", folder_path=folder.absolute_path+"/")
    user_folder = api_folder.add_folder(folder_name="user", folder_path=folder.absolute_path+"/")
    api_folder.add_folder(folder_name="dashboard", folder_path=folder.absolute_path+"/")


    


