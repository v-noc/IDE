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


def test_update_class(create_repos, create_class):
    class_service = ClassService(create_repos)
    create_class.name = "Updated Class"
    create_class.description = "This is an updated class"
    new_class = class_service.update(create_class)
    assert new_class is not None
    assert new_class.name == "Updated Class"
    assert new_class.description == "This is an updated class"


def test_delete_class(create_repos, create_class):
    class_service = ClassService(create_repos)
    class_service.delete(create_class.id)
    new_class = class_service.get(create_class.id)
    assert new_class is None


def test_add_function_to_class(create_repos, create_class, create_function):
    class_service = ClassService(create_repos)
    class_service.add_function_to_class(create_class.id, create_function.id)
    functions = class_service.get_children(create_class.id)
    assert len(functions) == 1

    assert functions[0]['vertex']['_id'] == create_function.id


def test_add_class_to_class(create_repos, create_class, create_class2):
    class_service = ClassService(create_repos)
    class_service.add_class_to_class(create_class.id, create_class2.id)
    classes = class_service.get_children(create_class.id)
    assert len(classes) == 1

    assert classes[0]['vertex']['_id'] == create_class2.id


def test_add_call_to_class(create_repos, create_class, create_call):
    class_service = ClassService(create_repos)
    class_service.add_call_to_class(create_class.id, create_call.id)
    calls = class_service.get_children(create_class.id)
    assert len(calls) == 1

    assert calls[0]['vertex']['_id'] == create_call.id
