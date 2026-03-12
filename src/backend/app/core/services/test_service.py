from app.db.context import ProjectUoW
from app.core.plugins.pytest_interceptor.runner import run_tests
from app.core.parser.jedi_adapter.manager import JediProjectManager
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScopeInfo:
    qname: str
    type: str           # "function" | "class" | "module"
    line_start: int
    line_end: int
    node_id: Optional[str] = None  # filled after DB lookup


class TestService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()
        self.jedi_manager = JediProjectManager(self.uow.project.path)

    def resolve_line_to_scopes(script, line: int) -> list[ScopeInfo]:
        """Return scope chain from innermost to file-level."""
        ctx = script.get_context(line, column=0)
        scopes = []

        while ctx:
            scopes.append(ScopeInfo(
                qname=ctx.name,  # parent name + current name
                type=ctx.type,  # "function" | "class" | "module"
                line_start=ctx.get_definition_start_position()[0],
                line_end=ctx.get_definition_end_position()[0],
            ))
            ctx = ctx.parent()

        return scopes

    async def run_tests(self, path: str):

        exit_code, coverage_datas = run_tests(path, self.uow.project.path)

        for coverage_data in coverage_datas:

            for f in coverage_data.tests:
                jedi = self.jedi_manager.get_script(f.file_name)
