from pathlib import Path
import hashlib
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.analyzer.symbol_collector.collector import SymbolCollector
from app.core.parser.analyzer.file_navigator import FileContainer
from app.core.parser.scope_manager.core import ScopeType
from arango.database import StandardDatabase
from app.core.model.nodes import BaseNode


class SymbolAnalyzer:
    def __init__(self, db: StandardDatabase):
        self.symbol_table = SymbolTable(db)
        self.symbol_table.scope_manager = ScopeManager()
        self.symbol_collector = SymbolCollector(self.symbol_table)

    def hydrate_from_project_structure(self, project_structure: list[dict]):
        """
        Populates the symbol table from an existing project structure.
        """
        for item in project_structure:
            vertex = item.get("vertex")
            if not vertex:
                continue

            node_type = vertex.get("node_type")
            qname = vertex.get("qname")

            if node_type and qname:
                # Simplified creation; in real code map
                # node_type to model class.
                node_instance = BaseNode(**vertex)
                self.symbol_table.qname_to_node[qname] = node_instance

    def create_project_node(
        self, project_name: str, project_description: str, project_path: str
    ):
        project_node = self.symbol_table.node_service["project"].create(
            name=project_name,
            description=project_description,
            path=project_path,
        )
        self.symbol_table.project_node = project_node
        self.symbol_table.qname_to_node[project_node.qname] = project_node

        self.symbol_table.scope_manager.create_root_scope(project_node.qname)
        return project_node

    def add_file(self, file_container: FileContainer):
        file_path = Path(file_container.file_path)
        project_root = Path(self.symbol_table.project_node.path)
        relative_path = file_path.relative_to(project_root)

        all_parts = relative_path.parts
        file_qname = (
            self.symbol_table.project_node.qname
            + "."
            + ".".join(all_parts[:-1] + (relative_path.stem,))
        )
        print(
            f"Adding file: {file_qname} to "
            f"{self.symbol_table.unprocessed_files} {file_path}"
        )
        self.symbol_table.file_containers[file_qname] = file_container
        self.symbol_table.unprocessed_files.append(file_qname)

        # Build and visualize hierarchy
        self._build_hierarchy_with_tree_view(relative_path, file_container)

    def build_symbol_table(self):
        for unprocessed_file in list(self.symbol_table.unprocessed_files):
            try:
                print(f"Analyzing file: {unprocessed_file}")

                scope = self.symbol_table.scope_manager.get_scope_by_qname(
                    unprocessed_file
                )

                self.symbol_table.scope_manager.enter_scope_by_scope(scope)
                file_node = self.symbol_table.file_containers[unprocessed_file]
                self.symbol_collector.context_analyze_symbols(file_node)
                self.symbol_table.scope_manager.exit_scope()
            except Exception as e:
                print(f"Error analyzing file: {unprocessed_file} {e}")
        print("Building finished")

    def _build_hierarchy_with_tree_view(
        self, file_path: Path, file_container: FileContainer
    ):
        """
        Builds the file hierarchy using a unified recursive function that
        correctly maintains nested scopes.
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
        self,
        path_parts: tuple,
        index: int,
        parent_qname: str,
        file_container: FileContainer,
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

        parent_node = self.symbol_table.qname_to_node[parent_qname]
        parent_node_service = self.symbol_table.node_service[parent_node.node_type]
        # --- Node Creation ---
        # This logic handles both folders and the final file.
        if current_qname not in self.symbol_table.qname_to_node:
            if is_last_part:
                # It's the file node
                print(f"{indent}📄 {part} (qname: {current_qname})")
                file_node_service = self.symbol_table.node_service["file"]

                # Calculate file hash
                try:
                    with open(file_container.file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    file_hash = hashlib.sha256(file_content.encode("utf-8")).hexdigest()
                except (IOError, UnicodeDecodeError):
                    file_hash = ""  # Fallback for non-readable files

                file_node = file_node_service.create(
                    part,
                    current_qname,
                    "file node",
                    path="/".join(path_parts),
                    hash=file_hash,
                )
                self.symbol_table.qname_to_node[current_qname] = file_node
                parent_node_service.add_file(parent_node.id, file_node.id)

            else:
                # It's a folder node
                print(f"{indent}📁 {part}/ (qname: {current_qname})")

                folder_node_service = self.symbol_table.node_service["folder"]
                folder_node = folder_node_service.create(
                    part,
                    current_qname,
                    "folder node",
                    path="/".join(path_parts[: index + 1]) + "/",
                )
                self.symbol_table.qname_to_node[current_qname] = folder_node
                parent_node_service.add_folder(parent_node.id, folder_node.id)

        else:
            # Node already exists
            existing_node = self.symbol_table.qname_to_node[current_qname]
            # Handle collision: if we need a folder here but a file already
            # occupies this qname, create a folder node for this qname and
            # attach it to the real parent.
            if not is_last_part and getattr(existing_node, "node_type", None) == "file":
                print(
                    f"{indent}📁 {part}/ (qname: {current_qname}) "
                    "[created to resolve file/folder name collision]"
                )
                folder_node_service = self.symbol_table.node_service["folder"]
                folder_node = folder_node_service.create(
                    part,
                    current_qname,
                    "folder node",
                    path="/".join(path_parts[: index + 1]) + "/",
                )
                # Point qname to folder for subsequent nesting
                self.symbol_table.qname_to_node[current_qname] = folder_node
                parent_node_service.add_folder(parent_node.id, folder_node.id)
            else:
                icon = "📄" if is_last_part else "📁"
                print(f"{indent}{icon} {part} (exists)")

        # --- THE CRITICAL SCOPE MANAGEMENT ---
        # 1. PUSH: Enter the scope for the current part (folder or file).
        self.symbol_table.scope_manager.enter_scope(
            current_name,
            ScopeType.MODULE,
        )

        if is_last_part:
            # 2a. DEEPEST POINT: If this is the file, we are now in the fully
            # nested scope. This is the correct place to collect symbols.
            self.symbol_collector.collect_symbols(file_container)
        else:
            # 2b. RECURSIVE STEP: If it's a folder, process the next part of
            # the path while still inside the current scope.
            self._build_path_recursive(
                path_parts,
                index + 1,
                current_qname,
                file_container,
            )

        # 3. POP: Exit the current scope. This happens on the way back up the
        # call stack, ensuring perfect pairing of enter/exit calls.
        self.symbol_table.scope_manager.exit_scope()
