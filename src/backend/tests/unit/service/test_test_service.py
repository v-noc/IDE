from dataclasses import dataclass

import pytest

from app.core.model.schemas.test_schema import _test_case_id, _test_link_id
from app.core.plugins.pytest_interceptor.coverage_plugin import CoverageData, TestData
from app.core.services.test_service import ScopeInfo, TestService


@dataclass
class _ScopeResolver:
    target_qname: str
    helper_qname: str

    def first_pass(self, _script, line: int, _column: int):
        if line == 10:
            return [
                ScopeInfo(self.target_qname, "function", 1, 200),
                ScopeInfo(self.helper_qname, "function", 1, 200),
            ]
        return [ScopeInfo(self.target_qname, "function", 1, 200)]

    def second_pass(self, _script, _line: int, _column: int):
        return [ScopeInfo(self.target_qname, "function", 1, 200)]


def _mock_coverage_data(test_id: str, file_name: str, lines):
    return CoverageData(
        test_id=test_id,
        tests=[TestData(file_name=file_name, lines=lines)],
    )


@pytest.mark.asyncio
async def test_build_documents_creates_test_case_and_links(create_sample_project):
    _, project_uow = create_sample_project
    service = TestService(project_uow)

    functions = await service.repos.code_element_repo.get_all(doc_type="FunctionSchema")
    assert len(functions) >= 2
    target_fn = functions[0]
    helper_fn = functions[1]

    resolver = _ScopeResolver("scope.target", "scope.helper")
    service._resolve_line_to_scopes = resolver.first_pass

    async def _resolve_ids(scope_coverages):
        scope_coverages["scope.target"].scope.node_id = target_fn.id
        scope_coverages["scope.helper"].scope.node_id = helper_fn.id

    service._resolve_scope_node_ids = _resolve_ids
    service._pick_target_function = lambda _node_id, _scopes: target_fn.id

    coverage = _mock_coverage_data(
        test_id="tests/test_main.py::test_target",
        file_name=target_fn.name,
        lines={10, 11},
    )
    test_cases, test_links = await service._build_documents([coverage])

    assert len(test_cases) == 1
    assert len(test_links) == 2
    assert test_cases[0]._id == _test_case_id(target_fn.id)
    assert {link._id for link in test_links} == {
        _test_link_id(test_cases[0]._id, target_fn.id),
        _test_link_id(test_cases[0]._id, helper_fn.id),
    }


@pytest.mark.asyncio
async def test_flush_batch_update_delete_and_get_by_owner(create_sample_project):
    _, project_uow = create_sample_project
    service = TestService(project_uow)

    functions = await service.repos.code_element_repo.get_all(doc_type="FunctionSchema")
    assert len(functions) >= 2
    target_fn = functions[0]
    helper_fn = functions[1]

    resolver = _ScopeResolver("scope.target", "scope.helper")
    service._pick_target_function = lambda _node_id, _scopes: target_fn.id

    async def _resolve_ids(scope_coverages):
        if "scope.target" in scope_coverages:
            scope_coverages["scope.target"].scope.node_id = target_fn.id
        if "scope.helper" in scope_coverages:
            scope_coverages["scope.helper"].scope.node_id = helper_fn.id

    service._resolve_scope_node_ids = _resolve_ids

    # First run inserts one test case and two links.
    service._resolve_line_to_scopes = resolver.first_pass
    first_coverage = _mock_coverage_data(
        test_id="tests/test_main.py::test_target",
        file_name=target_fn.name,
        lines={10, 11},
    )
    first_cases, first_links = await service._build_documents([first_coverage])
    first_batch = await service._prepare_batch_ops(first_cases, first_links)
    first_ok = await service.repos.test_repo.flush_batch(**first_batch)
    assert first_ok is True

    # Second run updates target link lines and removes helper link.
    service._resolve_line_to_scopes = resolver.second_pass
    second_coverage = _mock_coverage_data(
        test_id="tests/test_main.py::test_target",
        file_name=target_fn.name,
        lines={42},
    )
    second_cases, second_links = await service._build_documents([second_coverage])
    second_batch = await service._prepare_batch_ops(second_cases, second_links)

    second_ok = await service.repos.test_repo.flush_batch(**second_batch)
    assert second_ok is True

    test_case_id = _test_case_id(target_fn.id)
    target_link_id = _test_link_id(test_case_id, target_fn.id)
    helper_link_id = _test_link_id(test_case_id, helper_fn.id)

    case_doc = await service.repos.test_repo.get(test_case_id)
    assert case_doc is not None
    assert set(case_doc.get("test_links", set())) == {target_link_id}

    target_link_doc = await service.repos.test_repo.get(target_link_id)
    assert target_link_doc is not None
    assert set(target_link_doc.get("lines", set())) == {42}

    helper_link_doc = await service.repos.test_repo.get(helper_link_id)
    assert helper_link_doc is None

    cases_for_owner = await service.repos.test_repo.get_test_cases_for_node(target_fn.id)
    assert len(cases_for_owner) >= 1
    assert isinstance(cases_for_owner[0]["test_links"], list)
    assert isinstance(cases_for_owner[0]["test_links"][0], dict)
    assert set(cases_for_owner[0]["test_links"][0].get("lines", set())) == {42}


@pytest.mark.asyncio
async def test_run_tests_uses_mocked_runner(create_sample_project, monkeypatch):
    _, project_uow = create_sample_project
    service = TestService(project_uow)

    functions = await service.repos.code_element_repo.get_all(doc_type="FunctionSchema")
    assert len(functions) >= 1
    target_fn = functions[0]

    # service._resolve_line_to_scopes = lambda _script, _line, _column: [
    #     ScopeInfo("scope.target", "function", 1, 200),
    # ]

    async def _resolve_ids(scope_coverages):
        scope_coverages["scope.target"].scope.node_id = target_fn.id

    service._resolve_scope_node_ids = _resolve_ids
    service._pick_target_function = lambda _node_id, _scopes: target_fn.id

    mocked_cov = _mock_coverage_data(
        test_id="tests/test_main.py::test_target",
        file_name=target_fn.name,
        lines={7},
    )
    monkeypatch.setattr(
        "app.core.services.test_service.run_tests",
        lambda _path, _root, python_executable=None, command_prefix=None, test_root=None: (
            0,
            [mocked_cov],
            None,
            "",
        ),
    )

    result = await service.run_tests("tests/test_main.py")
    assert result["exit_code"] == 0
    assert result["test_cases"] == 1
    assert result["test_links"] == 1
    assert result["persisted"] is True
    assert result["error_message"] is None
    assert result["raw_output"] == ""
