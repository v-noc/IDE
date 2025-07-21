from app.core.manager import CodeGraphManager

import pprint

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

    # Sort children by name before asserting
    children = sorted(folder.get_folders(), key=lambda x: x.name)
    assert children[0].name == "api"
    assert children[1].name == "core"

    assert children[0].absolute_path == folder.absolute_path+"/api"
    assert children[1].absolute_path == folder.absolute_path+"/core"

def test_multi_level_nested_folder():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")
    folder = project.add_folder(folder_name="src", folder_path=project.absolute_path + "/")

    api_folder = folder.add_folder(folder_name="api", folder_path=folder.absolute_path+"/")
    user_folder = api_folder.add_folder(folder_name="user", folder_path=api_folder.absolute_path+"/")
    dashboard_folder = api_folder.add_folder(folder_name="dashboard", folder_path=api_folder.absolute_path+"/")

    assert len(project.get_folders()) == 1
    assert len(folder.get_folders()) == 1
    assert len(api_folder.get_folders()) == 2
    assert len(user_folder.get_folders()) == 0
    assert len(dashboard_folder.get_folders()) == 0

    assert user_folder.name == "user"
    assert dashboard_folder.name == "dashboard"
    assert user_folder.absolute_path == api_folder.absolute_path + "/user"
    assert dashboard_folder.absolute_path == api_folder.absolute_path + "/dashboard"

def test_get_descendant_tree():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")
    src_folder = project.add_folder(folder_name="src", folder_path=project.absolute_path + "/")
    api_folder = src_folder.add_folder(folder_name="api", folder_path=src_folder.absolute_path + "/")
    api_folder.add_file(file_name="health.py", file_path=api_folder.absolute_path + "/")
    user_folder = api_folder.add_folder(folder_name="user", folder_path=api_folder.absolute_path + "/")
    user_folder.add_file(file_name="user.py", file_path=user_folder.absolute_path + "/")

    tree = src_folder.get_descendant_tree()
    # pprint.pprint(project.get_descendant_tree())
    assert tree["name"] == "src"
    assert len(tree["children"]) == 1
    
    api_tree = tree["children"][0]
    assert api_tree["name"] == "api"
    assert len(api_tree["children"]) == 2

    # Sort children by name before asserting
    api_children = sorted(api_tree["children"], key=lambda x: x["name"])

    health_py_tree = api_children[0]
    assert health_py_tree["name"] == "health.py"
    assert len(health_py_tree["children"]) == 0

    user_tree = api_children[1]
    assert user_tree["name"] == "user"
    assert len(user_tree["children"]) == 1

    user_py_tree = user_tree["children"][0]
    assert user_py_tree["name"] == "user.py"
    assert len(user_py_tree["children"]) == 0