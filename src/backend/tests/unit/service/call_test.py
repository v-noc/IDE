from app.core.services.call_service import CallService
from app.core.model.properties import CodePosition


def test_create_call(create_repos, create_function):
    call_service = CallService(create_repos)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    new_call = call_service.create(
        "Test Call",
        "test_project.test_call",
        "This is a test call",

        position,
        create_function.id
    )
    assert new_call is not None
    assert new_call.name == "Test Call"
    assert new_call.qname == "test_project.test_call"
    assert new_call.description == "This is a test call"


def test_get_call(create_repos, create_call):
    call_service = CallService(create_repos)
    new_call = call_service.get(create_call.id)
    assert new_call is not None
    assert new_call.name == "Test Call"
    assert new_call.qname == "test_project.test_call"
    assert new_call.description == "This is a test call"


def test_update_call(create_repos, create_call):
    call_service = CallService(create_repos)
    create_call.name = "Updated Call"
    create_call.description = "This is an updated call"
    new_call = call_service.update(create_call)
    assert new_call is not None
    assert new_call.name == "Updated Call"
    assert new_call.description == "This is an updated call"


def test_delete_call(create_repos, create_call):
    call_service = CallService(create_repos)
    call_service.delete(create_call.id)
    new_call = call_service.get(create_call.id)
    assert new_call is None


def test_add_call_to_call(create_repos, create_call, create_call2):
    call_service = CallService(create_repos)
    call_service.add_call_to_call(create_call.id, create_call2.id)
    calls = call_service.get_children(create_call.id)
    assert len(calls) == 1
    assert calls[0]['vertex']['_id'] == create_call2.id
    assert calls[0]['target'] is not None
