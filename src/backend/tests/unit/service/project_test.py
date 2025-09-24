from app.core.services.project_service import ProjectService
from app.core.repository import Repositories


def test_create_project(create_repos):
    print("creating project test")

    project_service = ProjectService(
        create_repos
    )

    created_project = project_service.create(
        "Test Project",
        "This is a test project",
        "test_project"
    )

    assert created_project is not None
    assert created_project.name == "Test Project"
    assert created_project.qname == "test_project"
    assert created_project.description == "This is a test project"


def test_get_project(create_repos, create_project):
    print("getting project test")

    project_service = ProjectService(
        create_repos
    )

    projects = project_service.get_all()

    assert len(projects) == 1


def update_project(create_project, create_repos):

    project_service = ProjectService(
        create_repos
    )

    create_project.name = "Updated Project"
    create_project.description = "This is an updated project"
    create_project.path = "updated_project"

    updated_project = project_service.update(
        create_project
    )

    assert updated_project is not None
    assert updated_project.name == "Updated Project"
    assert updated_project.description == "This is an updated project"
    assert updated_project.path == "updated_project"


def test_delete_project(create_project, create_repos):
    project_service = ProjectService(
        create_repos
    )

    projects = project_service.get_all()

    project_service.delete(
        create_project.key
    )

    projects = project_service.get_all()

    assert len(projects) == 0


def test_add_folder_to_project(create_project, create_folder, create_repos):
    project_service = ProjectService(
        create_repos
    )

    project_service.add_folder_to_project(
        create_project.id,
        create_folder.id
    )

    children = project_service.get_children(
        create_project.id
    )

    assert len(children) == 1


def test_add_file_to_project(create_project, create_file, create_repos):
    project_service = ProjectService(
        create_repos
    )

    project_service.add_file_to_project(
        create_project.id,
        create_file.id
    )

    children = project_service.get_children(
        create_project.id
    )

    assert len(children) == 1
