from app.core.manager import CodeGraphManager

def test_project_creation(temp_project_dir):
    manager = CodeGraphManager()

    project = manager.create_project(name="test", path=temp_project_dir)
    assert project is not None
    assert project.name == "test"
    assert project.path == temp_project_dir
    