from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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
        self.jedi_manager = JediProjectManager(Path(self.uow.project.path))

    def create_test_config(
        self,
        enabled: bool,
        test_root: str,
        test_args: str = "",
        executable_path: Optional[str] = None,
    ):
        now = datetime.now(timezone.utc)
        return TestConfigSchema(
            _id=f"TestConfigSchema/{self.uow.project.db_name}",
            name="TestConfig",
            description="",
            enabled=enabled,
            test_root=test_root,
            test_args=test_args,
            executable_path=executable_path.strip() if executable_path else None,
            created_at=now,
            updated_at=now,
        )

    async def get_test_config(self):
        return await self.repos.test_repo.get_test_config(self.uow.project.db_name)

    async def create_or_update_config(
        self,
        enabled: bool,
        test_root: str,
        test_args: str = "",
        executable_path: Optional[str] = None,
    ) -> bool:
        config = self.create_test_config(
            enabled=enabled,
            test_root=test_root,
            test_args=test_args,
            executable_path=executable_path,
        )
        return await self.repos.test_repo.upsert_test_config(config)

    async def get_links_for_node(self, node_id: str):
        return await self.repos.test_repo.get_links_for_node(node_id)

    async def update_test_config(
        self,
        enabled: Optional[bool] = None,
        test_root: Optional[str] = None,
        test_args: Optional[str] = None,
        executable_path: Optional[str] = None,
    ):
        current = await self.get_test_config()

        if not current:
            return None

        now = datetime.now(timezone.utc)
        updated = TestConfigSchema(
            _id=current.get(
                "@id", f"TestConfigSchema/{self.uow.project.db_name}"),
            name=current.get("name", "TestConfig"),
            description=current.get("description", ""),
            enabled=current.get(
                "enabled", False) if enabled is None else enabled,
            test_root=current.get(
                "test_root", "") if test_root is None else test_root,
            test_args=current.get(
                "test_args", "") if test_args is None else test_args,
            executable_path=(
                current.get("executable_path")
                if executable_path is None
                else (executable_path.strip() or None)
            ),
            created_at=current.get("created_at", now),
            updated_at=now,
        )
        ok = await self.repos.test_repo.upsert_test_config(updated)
        if not ok:
            return None
        return await self.get_test_config()

    async def delete_test_config(self) -> bool:
        return await self.repos.test_repo.delete_test_config(self.uow.project.db_name)

    async def get_test_cases_for_node(self, node_id: str):
        return await self.repos.test_repo.get_test_cases_for_node(node_id)

    async def run_tests_for_owner(self, owner_id: str):
        test_cases = await self.get_test_cases_for_node(owner_id)
        if not test_cases:
            return {
                "runs": [],
                "total_runs": 0,
                "total_test_cases": 0,
                "total_test_links": 0,
            }

        run_targets = []
        seen_targets = set()
        for case in test_cases:
            target = case.get("node_id") or case.get("path")
            if not target or target in seen_targets:
                continue
            seen_targets.add(target)
            run_targets.append(target)

        runs = []
        for target in run_targets:
            runs.append(await self.run_tests(target))

        return {
            "runs": runs,
            "total_runs": len(runs),
            "total_test_cases": sum(item.get("test_cases", 0) for item in runs),
            "total_test_links": sum(item.get("test_links", 0) for item in runs),
        }

    @staticmethod
    def _resolve_line_to_scopes(script, line: int, column: int) -> list[ScopeInfo]:
        """
        Resolve a covered line to scope chain from inner scope -> module.
        """
        ctx = script.get_context(line, column=column)
        scopes: list[ScopeInfo] = []

        qname = TestService._get_qname(ctx)

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

        return scopes

    @staticmethod
    def _get_qname(node_name):
        if hasattr(node_name, "get_qualified_names"):
            qnames = node_name.get_qualified_names(True)
            if qnames:
                qualified_name = ".".join(qnames)
                return qualified_name

        if hasattr(node_name, "full_name"):
            return node_name.full_name

        if hasattr(node_name, "tree_node"):
            return TestService._get_qname(node_name.parent_context) + "." + node_name.tree_node.name
        return None

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

        for cov in function_coverages:
            if cov.scope.qname.split(".")[-1] == raw_name:
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
                        source = Path(file_coverage.file_name).read_text()
                        lines = source.splitlines()

                        # Jedi uses 1-based indexing for lines
                        target_line = lines[line - 1]

                        # Find the first non-whitespace character index (the "real" column)
                        # This skips the spaces/tabs and puts Jedi right in the action
                        active_column = len(target_line) - \
                            len(target_line.lstrip())
                        scopes = self._resolve_line_to_scopes(
                            script, line, active_column)

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

    @staticmethod
    def _normalize_doc_id(value) -> Optional[str]:
        """Normalize Terminus ids to `Type/key` form for comparisons."""
        if value is None:
            return None
        if isinstance(value, dict):
            value = value.get("@id")
        if not isinstance(value, str):
            return None
        prefix = "terminusdb:///data/"
        if value.startswith(prefix):
            return value[len(prefix):]
        return value

    async def _prepare_batch_ops(
        self,
        test_cases: list[TestCaseSchema],
        test_links: list[TestLinkSchema],
    ):
        # 1. Normalize and identify all target IDs
        case_ids = [case._id for case in test_cases]
        new_link_by_id = {link._id: link for link in test_links}
        all_link_ids = list(new_link_by_id.keys())

        # 2. Fetch everything that actually exists in the DB
        existing_cases_raw = await self.repos.test_repo.get_by_ids(case_ids)
        existing_links_raw = await self.repos.test_repo.get_by_ids(all_link_ids)

        # 3. Create lookup maps with normalized IDs
        existing_case_by_id = {
            self._normalize_doc_id(raw.get("@id")): raw
            for raw in existing_cases_raw if raw.get("@id")
        }
        existing_link_ids = {
            self._normalize_doc_id(raw.get("@id"))
            for raw in existing_links_raw if raw.get("@id")
        }

        # 4. Map existing relationships for deletion logic
        delete_link_parent: dict[str, str] = {}
        for case_id, case_doc in existing_case_by_id.items():
            for raw_link_id in case_doc.get("test_links", []) or []:
                link_id = self._normalize_doc_id(raw_link_id)
                if link_id:
                    delete_link_parent[link_id] = case_id

        # 5. Categorize Links: Insert vs Update
        new_link_ids_set = set(new_link_by_id.keys())
        link_inserts = [
            new_link_by_id[lid] for lid in (new_link_ids_set - existing_link_ids)
        ]
        link_updates = [
            new_link_by_id[lid] for lid in (new_link_ids_set & existing_link_ids)
        ]

        # Links to delete: were in the old cases but aren't in the new test run
        # Note: This logic assumes a "replace" strategy for a test case's links
        current_run_link_ids = set(new_link_by_id.keys())
        link_deletes = [
            lid for lid in delete_link_parent.keys() if lid not in current_run_link_ids
        ]

        # 6. Categorize Cases
        case_inserts = [
            c for c in test_cases if c._id not in existing_case_by_id]
        case_updates = [c for c in test_cases if c._id in existing_case_by_id]

        insert_link_parent = {}
        for case in test_cases:
            for link_id in case.test_links:
                insert_link_parent[link_id] = case._id

        return {
            "case_inserts": case_inserts,
            "case_updates": case_updates,
            "link_inserts": link_inserts,
            "link_updates": link_updates,
            "link_deletes": link_deletes,
            "insert_link_parent": insert_link_parent,
            "delete_link_parent": delete_link_parent,
        }

    async def run_tests(self, path: str, python_executable: Optional[str] = None):
        test_path = path
        if not os.path.isabs(test_path):
            test_path = os.path.join(self.uow.project.path, test_path)

        config = await self.get_test_config()
        if python_executable is None and config:
            python_executable = config.get("executable_path")
        test_root = config.get("test_root", "") if config else None

        exit_code, coverage_datas, error_message, raw_output = run_tests(
            test_path,
            self.uow.project.path,
            python_executable=python_executable,
            command_prefix=None,
            test_root=test_root or None,
        )

        test_cases, test_links = await self._build_documents(coverage_datas)

        batch_ops = await self._prepare_batch_ops(test_cases, test_links)
        batch_ok = await self.repos.test_repo.flush_batch(**batch_ops)
        return {
            "exit_code": exit_code,
            "test_cases": len(test_cases),
            "test_links": len(test_links),
            "persisted": batch_ok,
            "error_message": error_message,
            "raw_output": raw_output,
        }
