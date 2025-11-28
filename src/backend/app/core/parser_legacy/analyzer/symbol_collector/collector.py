import ast
import os
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.analyzer.file_navigator import FileContainer
from app.core.parser.analyzer.symbol_collector.node_handlers import (
    ImportHandler,
    CallHandler,
    AssignmentHandler,
    FunctionHandler,
    ClassHandler,
)
from app.core.parser.ast.models import BaseSchema, SchemaType
from app.core.parser.scope_manager.core.scope import ScopeType
from app.core.model.properties import CodePosition


class SymbolCollector:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

        self.import_handler = ImportHandler(symbol_table)
        self.call_handler = CallHandler(
            symbol_table, self._analyze_node_context_recursive
        )
        self.assignment_handler = AssignmentHandler(
            symbol_table, call_handler=self.call_handler
        )
        self.function_handler = FunctionHandler(symbol_table)
        self.class_handler = ClassHandler(symbol_table, self.function_handler)
        self.current_file_path = ""

    def collect_symbols(self, file_node: FileContainer):
        for node in file_node.parsed_nodes:
            self._collect_symbols_recursive(node)
        # After collecting all top-level symbols, prune stale direct children
        current_scope_qname = (
            self.symbol_table.scope_manager.current_scope.qualified_name
        )
        self._prune_stale_direct_children(
            current_scope_qname, file_node.parsed_nodes)

    def _collect_symbols_recursive(self, node: BaseSchema):
        if node.schema_type == SchemaType.FUNCTION:
            self.symbol_table.scope_manager.enter_scope(
                node.name, ScopeType.FUNCTION)

            self.function_handler.handle_function_node(node)
            for child in node.children:
                self._collect_symbols_recursive(child)
            # Prune stale direct children under this function scope
            current_scope_qname = (
                self.symbol_table.scope_manager.current_scope.qualified_name
            )
            self._prune_stale_direct_children(
                current_scope_qname, node.children)
            self.symbol_table.scope_manager.exit_scope()

        elif node.schema_type == SchemaType.CLASS:
            self.symbol_table.scope_manager.enter_scope(
                node.name, ScopeType.CLASS)

            self.class_handler.handle_class_node(node)
            for child in node.children:
                self._collect_symbols_recursive(child)
            # Prune stale direct children under this class scope
            current_scope_qname = (
                self.symbol_table.scope_manager.current_scope.qualified_name
            )
            self._prune_stale_direct_children(
                current_scope_qname, node.children)
            self.symbol_table.scope_manager.exit_scope()

    def context_analyze_symbols(self, file_node: FileContainer):
        # Normalize current file path so __init__.py uses the parent package scope
        curr = self.symbol_table.scope_manager.current_scope.qualified_name
        # if self.symbol_table.scope_manager.current_scope.scope_type == ScopeType.MODULE and curr.endswith(".__init__"):
        #     curr = curr[: -len(".__init__")]
        self.current_file_path = curr
        if self.current_file_path in self.symbol_table.unprocessed_files:
            self.symbol_table.unprocessed_files.remove(self.current_file_path)
        else:
            print(f"File {self.current_file_path} already processed")
            return
        for node in file_node.parsed_nodes:
            self._analyze_node_context_recursive(node)
        # After analyzing the file context, prune stale direct calls across all
        # recorded parents (file, functions/classes, nested call nodes)
        self.symbol_table.prune_all_recorded_calls()

    def _analyze_node_context_recursive(self, node: BaseSchema):
        try:
            print(
                f"Analyzing node: {node.schema_type} - {self.current_file_path} - {self.symbol_table.scope_manager.current_scope.qualified_name}"
            )

            if node.schema_type == SchemaType.IMPORT:
                imported_modules = self.import_handler.handle_import_node(node)

                for imported_module in imported_modules:
                    file_node = self.symbol_table.file_containers.get(
                        imported_module)
                    if file_node is None:
                        imported_module = f"{imported_module}.__init__"
                        file_node = self.symbol_table.file_containers.get(
                            imported_module
                        )
                    if (
                        file_node is None
                        or imported_module not in self.symbol_table.unprocessed_files
                    ):
                        continue

                    scope = self.symbol_table.scope_manager.get_scope_by_qname(
                        imported_module
                    )
                    current_scope = self.symbol_table.scope_manager.current_scope
                    self.symbol_table.scope_manager.enter_scope_by_scope(scope)
                    self.context_analyze_symbols(file_node)

                    self.symbol_table.scope_manager.exit_scope()
                    self.symbol_table.scope_manager.enter_scope_by_scope(
                        current_scope)

            elif node.schema_type == SchemaType.IMPORT_FROM:
                imported_modules = self.import_handler.handle_import_from_node(
                    node)
                try:
                    for imported_module in imported_modules:
                        file_node = self.symbol_table.file_containers.get(
                            imported_module
                        )
                        if file_node is None:
                            imported_module = f"{imported_module}.__init__"
                            file_node = self.symbol_table.file_containers.get(
                                imported_module
                            )

                        if (
                            file_node is None
                            or imported_module
                            not in self.symbol_table.unprocessed_files
                        ):
                            continue
                        current_scope = self.symbol_table.scope_manager.current_scope
                        scope = self.symbol_table.scope_manager.get_scope_by_qname(
                            imported_module
                        )
                        self.symbol_table.scope_manager.enter_scope_by_scope(
                            scope)
                        self.context_analyze_symbols(file_node)
                        self.symbol_table.scope_manager.exit_scope()
                        self.symbol_table.scope_manager.enter_scope_by_scope(
                            current_scope
                        )
                    self.import_handler.process_import_from(node)

                except Exception as e:
                    print(f"Error analyzing import from node: {e}")
                    return

            elif (
                node.schema_type == SchemaType.FUNCTION
                or node.schema_type == SchemaType.CLASS
            ):
                curr = self.symbol_table.scope_manager.current_scope.qualified_name
                qname = f"{curr}.{node.name}"
                scope = self.symbol_table.scope_manager.get_scope_by_qname(
                    qname)

                if scope:
                    self.symbol_table.scope_manager.enter_scope_by_scope(scope)

                    if node.schema_type == SchemaType.CLASS:
                        self.class_handler.handle_inherit_class_node(node)
                    for child in node.children:
                        self._analyze_node_context_recursive(child)

                    self.symbol_table.scope_manager.exit_scope()

            elif node.schema_type == SchemaType.CALL:
                current_frame = (
                    self.symbol_table.scope_manager.call_tracker.current_frame
                )

                if (
                    current_frame
                    and current_frame.callee_symbol.qualified_name
                    != self.symbol_table.scope_manager.current_scope.qualified_name
                ):
                    return

                self.call_handler.handle_call(node)

            elif node.schema_type == SchemaType.ASSIGN:
                pass
                self.assignment_handler.handle_assign_node(node)
            elif node.schema_type == SchemaType.ANN_ASSIGN:
                pass
                self.assignment_handler.handle_ann_assign_node(node)
        except Exception as e:
            print(f"Error analyzing node: {node.schema_type} {e}")
            return

    def _prune_stale_direct_children(
        self, container_qname: str, parsed_children: list[BaseSchema]
    ) -> None:
        """
        Delete direct function/class children under the given container qname.

        Uses depth=1 containment queries to fetch only immediate children.
        """
        container_node = self.symbol_table.qname_to_node.get(container_qname)
        if not container_node:
            return

        # Build expected direct children qnames from parsed children
        expected_qnames: set[str] = set()
        for child in parsed_children:
            if child.schema_type in (SchemaType.FUNCTION, SchemaType.CLASS):
                expected_qnames.add(f"{container_qname}.{child.name}")

        node_type = getattr(container_node, "node_type", None)
        if node_type not in ("file", "class", "function"):
            return

        # Select proper repo through services so we can pass depth=1
        if node_type == "file":
            repo = self.symbol_table.node_service["file"].repos.file_repo
        elif node_type == "class":
            repo = self.symbol_table.node_service["class"].repos.class_repo
        else:
            service = self.symbol_table.node_service["function"]
            repo = service.repos.function_repo

        children = (
            repo.get_containment_tree(
                container_node.id,
                depth=1,
            )
            or []
        )

        stale_keys: list[tuple[str, str]] = []
        for item in children:
            vertex = item.get("vertex") or {}
            parent_id = item.get("parent_id")
            if parent_id != container_node.id:
                continue  # only immediate children
            child_type = vertex.get("node_type")
            if child_type not in ("function", "class"):
                continue
            qname = vertex.get("qname")
            if qname and qname not in expected_qnames:
                key = vertex.get("_key")
                if key:
                    stale_keys.append((child_type, key))

        for child_type, key in stale_keys:
            try:
                if child_type == "function":
                    self.symbol_table.node_service["function"].delete(key)
                else:
                    self.symbol_table.node_service["class"].delete(key)
            except Exception:
                continue
