from app.core.manager import CodeGraphManager

def test_project_loading(create_project):
    project = create_project
    
    manager = CodeGraphManager()
    projects = manager.get_all_projects()
    assert len(projects) == 1

    assert project is not None
    assert project.name == "test"
    assert project.path == "/path/to/project"
    assert project.get_files() == []
    assert project.get_folders() == []
    
def test_get_project(create_project):
    project = create_project

    manager = CodeGraphManager()
    loaded_project = manager.load_project(project_key=project.key)
    assert loaded_project is not None
    assert loaded_project.name == "test"
    assert loaded_project.path == "/path/to/project"
    assert loaded_project.get_files() == []
    assert loaded_project.get_folders() == []
    
