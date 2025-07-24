# tests/unit/core/test_manager.py

from app.core.manager import CodeGraphManager

def test_get_all_projects(temp_project_dir):
    """
    Tests that the get_all_projects method correctly retrieves all projects
    from the database.
    """
    # 1. Arrange
    manager = CodeGraphManager()
    manager.create_project(name="project1", path=f"{temp_project_dir}/project1")
    manager.create_project(name="project2", path=f"{temp_project_dir}/project2")

    # 2. Act
    projects = manager.get_all_projects()

    # 3. Assert
    assert len(projects) == 2
    project_names = {p.name for p in projects}
    assert "project1" in project_names
    assert "project2" in project_names
