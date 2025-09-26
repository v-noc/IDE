from pathlib import Path
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.analyzer.symbol_collector.collector import SymbolCollector
from app.models.node import FileNode, FolderNode, ProjectNode
from app.core.parser.analyzer.file_navigator import FileContainer
from app.core.parser.scope_manager.core import ScopeType


class SymbolAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.symbol_table.scope_manager = ScopeManager()
        self.symbol_collector = SymbolCollector(self.symbol_table)

    def create_project_node(self, project_name: str, project_qname: str, project_path: str):
        schema = ProjectNode(
            name=project_name,
            qname=project_qname,
            path=project_path
        )
        self.symbol_table.project_node = schema

        self.symbol_table.scope_manager.create_root_scope(
            project_qname
        )

    def add_file(self, file_container: FileContainer):
        file_path = Path(file_container.file_path)
        all_parts = file_path.parts
        file_qname = self.symbol_table.project_node.qname + \
            "." + ".".join(all_parts[:-1] + (file_path.stem,))
        print(
            f"Adding file: {file_qname} to {self.symbol_table.unprocessed_files} {file_path}")
        self.symbol_table.file_nodes[file_qname] = file_container
        self.symbol_table.unprocessed_files.append(file_qname)

        # Build and visualize hierarchy
        self._build_hierarchy_with_tree_view(file_path, file_container)

    def _build_hierarchy_with_tree_view(self, file_path: Path, file_container: FileContainer):
        """
        Builds the file hierarchy using a unified recursive function
        that correctly maintains nested scopes.
        """
        print(f"\n🌳 Building hierarchy for: {file_path}")
        all_parts = file_path.parts
        if not all_parts:
            return

        # Start the recursive process from the project root.
        self._build_path_recursive(
            all_parts, 0, self.symbol_table.project_node.qname, file_container
        )

    def _build_path_recursive(
        self, path_parts: tuple, index: int, parent_qname: str, file_container: FileContainer
    ):
        """
        Processes one part of the path, enters its scope, and recursively
        calls itself for the next part, ensuring scopes are nested.

        This is the core of the correct logic.
        """
        # Base Case: We've processed all parts of the path. We are done.
        if index >= len(path_parts):
            return

        part = path_parts[index]
        is_last_part = index == len(path_parts) - 1
        indent = "  " * index

        # Determine qname for the current node.
        # The file's qname should use the stem (name without extension).
        current_name = Path(part).stem if is_last_part else part
        current_qname = f"{parent_qname}.{current_name}"

        # --- Node Creation ---
        # This logic handles both folders and the final file.
        if current_qname not in self.symbol_table.qname_to_node:
            if is_last_part:
                # It's the file node
                print(f"{indent}📄 {part} (qname: {current_qname})")
                file_schema = FileNode(
                    name=part,
                    path="/".join(path_parts),
                    qname=current_qname,
                    parent_qname=parent_qname,
                )
                self.symbol_table.qname_to_node[current_qname] = file_schema

            else:
                # It's a folder node
                print(f"{indent}📁 {part}/ (qname: {current_qname})")
                folder_schema = FolderNode(
                    name=part,
                    qname=current_qname,
                    path="/".join(path_parts[: index + 1]) + "/",
                    parent_qname=parent_qname,
                )
                self.symbol_table.qname_to_node[current_qname] = folder_schema

            # Link the parent to the new node
            # self.symbol_table.contains.append(
            #     Contains(from_qname=parent_qname, to_qname=current_qname)
            # )
        else:
            # Node already exists
            icon = "📄" if is_last_part else "📁"
            print(f"{indent}{icon} {part} (exists)")

        # --- THE CRITICAL SCOPE MANAGEMENT ---
        # 1. PUSH: Enter the scope for the current part (folder or file).
        self.symbol_table.scope_manager.enter_scope(
            current_name, ScopeType.MODULE)

        if is_last_part:
            # 2a. DEEPEST POINT: If this is the file, we are now in the fully
            # nested scope. This is the correct place to collect symbols.
            self.symbol_collector.collect_symbols(file_container)
        else:
            # 2b. RECURSIVE STEP: If it's a folder, process the next part of the path
            # *while still inside the current scope*.
            self._build_path_recursive(
                path_parts, index + 1, current_qname, file_container)

        # 3. POP: Exit the current scope. This happens on the way back up the
        # call stack, ensuring perfect pairing of enter/exit calls.
        self.symbol_table.scope_manager.exit_scope()
