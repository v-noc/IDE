from typing import Optional
from pathlib import Path
from arango.database import StandardDatabase
from app.core.parser.analyzer.file_navigator import FileNavigator
from app.core.parser.ast.scanner import scan
from app.core.parser.analyzer.symbol_analyzer import SymbolAnalyzer
from app.core.model.nodes import ProjectNode
from app.core.parser.analyzer.file_navigator import FileContainer


class GraphBuilder:
    def __init__(
        self,
        project_path: str,
        db: StandardDatabase,
        ignore_file_name: str = ".gitignore",
        project_node: Optional[ProjectNode] = None,
    ):
        self.project_path = Path(project_path)
        self.ignore_file_name = ignore_file_name
        self.db = db
        self.symbol_analyzer = SymbolAnalyzer(db)
        if project_node:
            self.symbol_analyzer.symbol_table.project_node = project_node
            self.project_node = project_node
            self.symbol_analyzer.symbol_table.qname_to_node[project_node.qname] = (
                project_node
            )
            self.symbol_analyzer.symbol_table.scope_manager.create_root_scope(
                project_node.qname
            )
            # Hydrate the symbol table with the existing project structure
            project_service = self.symbol_analyzer.symbol_table.node_service["project"]
            project_structure = project_service.get_project_structure(
                project_node.id)
            self.symbol_analyzer.hydrate_from_project_structure(
                project_structure)
        else:
            self.project_node = None

    def build(self, project_name: str, project_description: str):
        if not self.project_node:
            self.project_node = self.symbol_analyzer.create_project_node(
                project_name, project_description, str(self.project_path)
            )

        file_navigator = FileNavigator(
            self.project_path, self.ignore_file_name)
        python_files = file_navigator.find_files(extensions=[".py"])

        for file_path in python_files:
            with open(file_path, "r") as file:
                file_content = file.read()
            ast_scanner = scan(file_content, file_path)
            file_name = Path(file_path)

            relative_path = file_name.relative_to(self.project_path)

            file_container = FileContainer(
                file_path=str(file_path),
                file_name=file_name.stem,
                parsed_nodes=ast_scanner,
            )

            self.symbol_analyzer.add_file(file_container)
        self.symbol_analyzer.build_symbol_table()
