from app.core.services.class_service import ClassService
from app.core.model.properties import CodePosition


def test_create_class(create_repos):
    class_service = ClassService(create_repos)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    new_class = class_service.create(
        "Test Class",
        "test_project.test_class",
        "This is a test class",
        "test_class",
        position
    )
    assert new_class is not None
    assert new_class.name == "Test Class"
    assert new_class.qname == "test_project.test_class"
    assert new_class.description == "This is a test class"


def test_get_class(create_repos, create_class):
    class_service = ClassService(create_repos)
    new_class = class_service.get(create_class.id)
    assert new_class is not None
    assert new_class.name == "Test Class"
    assert new_class.qname == "test_project.test_class"
    assert new_class.description == "This is a test class"
