from app.core.manager import CodeGraphManager

def test_project_creation(temp_project_dir):
    manager = CodeGraphManager()
    projects = manager.get_all_projects()
    assert len(projects) == 0
    
    project = manager.create_project(name="test", path=temp_project_dir)
    assert project is not None

   
    assert project.name == "test"
    assert project.path == temp_project_dir
    assert project.get_files() == []
    assert project.get_folders() == []

