from dataclasses import dataclass
from datetime import datetime, timezone
import os
import re
from typing import Optional

from app.core.model.schemas.test_schema import (
    TestCaseSchema,
    TestConfigSchema,
    TestLinkSchema,
    _test_case_id,
    _test_link_id,
)
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.plugins.pytest_interceptor.runner import run_tests
from app.db.context import ProjectUoW


@dataclass
class ScopeInfo:
    qname: str
    type: str  # "function" | "class" | "module"
    line_start: int
    line_end: int
    node_id: Optional[str] = None


@dataclass
class ScopeCoverage:
    scope: ScopeInfo
    lines: set[int]


class TestService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()
        self.jedi_manager = JediProjectManager(self.uow.project.path)

    def create_test_config(self, enabled: bool, test_root: str, test_args: str = ""):
        now = datetime.now(timezone.utc)
        return TestConfigSchema(
            _id=f"TestConfigSchema/{self.uow.project.db_name}",
            name="TestConfig",
            description="",
            enabled=enabled,
            test_root=test_root,
            test_args=test_args,
            created_at=now,
            updated_at=now,
        )

    async def get_test_config(self):
        return await self.repos.test_repo.get_test_config(self.uow.project.db_name)

    async def get_test_cases_for_node(self, node_id: str):
        return await self.repos.test_repo.get_test_cases_for_node(node_id)

    def get_test_coverage_for_node(self, node_id: str):
        return self.get_test_cases_for_node(node_id)

    @staticmethod
    def _resolve_line_to_scopes(script, line: int) -> list[ScopeInfo]:
        """
        Resolve a covered line to scope chain from inner scope -> module.
        """
        ctx = script.get_context(line, column=0)
        scopes: list[ScopeInfo] = []
        while ctx:
            qname = getattr(ctx, "full_name", None) or getattr(
                ctx, "name", None)
            if qname:
                start_pos = ctx.get_definition_start_position() or (line, 0)
                end_pos = ctx.get_definition_end_position() or (line, 0)
                scopes.append(
                    ScopeInfo(
                        qname=qname,
                        type=ctx.type,
                        line_start=start_pos[0],
                        line_end=end_pos[0],
                    )
                )
            ctx = ctx.parent()
        return scopes

    async def _resolve_scope_node_ids(self, scope_coverages: dict[str, ScopeCoverage]) -> None:
        function_qnames = [
            qname for qname, cov in scope_coverages.items() if cov.scope.type == "function"
        ]
        class_qnames = [
            qname for qname, cov in scope_coverages.items() if cov.scope.type == "class"
        ]
        module_qnames = [
            qname for qname, cov in scope_coverages.items() if cov.scope.type == "module"
        ]

        function_nodes = await self.repos.code_element_repo.get_by_qnames(function_qnames, doc_type="FunctionSchema")
        class_nodes = await self.repos.code_element_repo.get_by_qnames(class_qnames, doc_type="ClassSchema")
        file_nodes = await self.repos.structure_repo.get_by_qnames(module_qnames, doc_type="FileSchema")

        function_by_qname = {node.qname: node for node in function_nodes}
        class_by_qname = {node.qname: node for node in class_nodes}

        for qname, coverage in scope_coverages.items():
            if coverage.scope.type == "function":
                node = function_by_qname.get(qname)
                coverage.scope.node_id = node.id if node else None
            elif coverage.scope.type == "class":
                node = class_by_qname.get(qname)
                coverage.scope.node_id = node.id if node else None
            elif coverage.scope.type == "module":
                node = file_nodes.get(qname)
                coverage.scope.node_id = node.id if node else None

    @staticmethod
    def _pick_target_function(node_id: str, scope_coverages: dict[str, ScopeCoverage]) -> Optional[str]:
        function_coverages = [
            cov for cov in scope_coverages.values()
            if cov.scope.type == "function" and cov.scope.node_id
        ]
        if not function_coverages:
            return None

        raw_name = node_id.split("::")[-1]
        # remove parametrized suffix
        raw_name = re.sub(r"\[.*\]$", "", raw_name)
        candidate = raw_name[5:] if raw_name.startswith("test_") else raw_name

        for cov in function_coverages:
            if cov.scope.qname.split(".")[-1] == candidate:
                return cov.scope.node_id

        most_covered = max(function_coverages, key=lambda cov: len(cov.lines))
        return most_covered.scope.node_id

    async def _build_documents(self, coverage_datas):
        test_case_by_id: dict[str, TestCaseSchema] = {}
        test_link_by_id: dict[str, TestLinkSchema] = {}
        now = datetime.now(timezone.utc)

        for coverage_data in coverage_datas:
            scope_coverages: dict[str, ScopeCoverage] = {}

            for file_coverage in coverage_data.tests:
                try:
                    script = self.jedi_manager.get_script(
                        file_coverage.file_name)
                except Exception:
                    continue

                for line in sorted(file_coverage.lines):
                    try:
                        scopes = self._resolve_line_to_scopes(script, line)
                    except Exception:
                        continue
                    for scope in scopes:
                        item = scope_coverages.get(scope.qname)
                        if item is None:
                            scope_coverages[scope.qname] = ScopeCoverage(
                                scope=scope, lines={line})
                        else:
                            item.lines.add(line)

            if not scope_coverages:
                continue

            await self._resolve_scope_node_ids(scope_coverages)

            target_function_id = self._pick_target_function(
                coverage_data.test_id, scope_coverages)
            if not target_function_id:
                continue

            test_case_id = _test_case_id(target_function_id)
            test_path = coverage_data.test_id.split("::")[0]
            test_case = test_case_by_id.get(test_case_id)
            if test_case is None:
                test_case = TestCaseSchema(
                    _id=test_case_id,
                    name=coverage_data.test_id,
                    description="",
                    node_id=coverage_data.test_id,
                    path=test_path,
                    target_function=target_function_id,
                    test_links=set(),
                    created_at=now,
                    updated_at=now,
                )
                test_case_by_id[test_case_id] = test_case
            else:
                test_case.node_id = coverage_data.test_id
                test_case.path = test_path
                test_case.updated_at = now

            for cov in scope_coverages.values():
                if not cov.scope.node_id:
                    continue

                link_id = _test_link_id(test_case_id, cov.scope.node_id)
                existing_link = test_link_by_id.get(link_id)
                if existing_link:
                    existing_link.lines.update(cov.lines)
                    existing_link.updated_at = now
                else:
                    owner_function = cov.scope.node_id if cov.scope.type == "function" else None
                    owner_class = cov.scope.node_id if cov.scope.type == "class" else None
                    owner_file = cov.scope.node_id if cov.scope.type == "module" else None
                    test_link_by_id[link_id] = TestLinkSchema(
                        _id=link_id,
                        name=f"coverage:{cov.scope.qname}",
                        description="",
                        lines=set(cov.lines),
                        owner_function=owner_function,
                        owner_class=owner_class,
                        owner_file=owner_file,
                        created_at=now,
                        updated_at=now,
                    )
                test_case.test_links.add(link_id)

        return list(test_case_by_id.values()), list(test_link_by_id.values())

    async def run_tests(self, path: str):
        test_path = path
        if not os.path.isabs(test_path):
            test_path = os.path.join(self.uow.project.path, test_path)
        exit_code, coverage_datas = run_tests(test_path, self.uow.project.path)
        test_cases, test_links = await self._build_documents(coverage_datas)
        batch_ok = await self.repos.test_repo.flush_batch(test_cases, test_links)
        return {
            "exit_code": exit_code,
            "test_cases": len(test_cases),
            "test_links": len(test_links),
            "persisted": batch_ok,
        }
