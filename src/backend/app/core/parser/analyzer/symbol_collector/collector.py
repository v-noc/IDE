from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.analyzer.file_navigator import FileContainer
from app.core.parser.analyzer.symbol_collector.node_handlers import (
    ImportHandler, CallHandler, AssignmentHandler, FunctionHandler, ClassHandler)
from app.core.parser.ast.models import BaseSchema, SchemaType
from app.core.parser.scope_manager.core.scope import ScopeType


class SymbolCollector:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

        self.import_handler = ImportHandler(symbol_table, self.import_resolver)
        self.call_handler = CallHandler(
            symbol_table, self._analyze_node_recursive)
        self.assignment_handler = AssignmentHandler(
            symbol_table, call_handler=self.call_handler)
        self.function_handler = FunctionHandler(symbol_table)
        self.class_handler = ClassHandler(symbol_table)
        self.current_file_path = ""

    def collect_symbols(self, file_node: FileContainer):
        for node in file_node.parsed_nodes:
            self._collect_symbols_recursive(node)

    def _collect_symbols_recursive(self, node: BaseSchema):
        if node.node_type == SchemaType.FUNCTION:
            self.symbol_table.scope_manager.enter_scope(
                node.name, ScopeType.FUNCTION)

            current_scope = self.symbol_table.scope_manager.current_scope
            qname = f"{current_scope.qualified_name}"

            self.symbol_table.qname_to_node[qname] = node
            self.function_handler.handle_function_node(node, qname)
            for child in node.children:
                self._collect_symbols_recursive(child)

            self.symbol_table.scope_manager.exit_scope()

        elif node.node_type == SchemaType.CLASS:
            self.symbol_table.scope_manager.enter_scope(
                node.name, ScopeType.CLASS)

            current_scope = self.symbol_table.scope_manager.current_scope
            qname = f"{current_scope.qualified_name}"

            self.symbol_table.qname_to_node[qname] = node
            for child in node.children:
                self._collect_symbols_recursive(child)
            self.symbol_table.scope_manager.exit_scope()

    def context_analyze_symbols(self, file_node: FileContainer):
        self.current_file_path = self.symbol_table.scope_manager.current_scope.qualified_name
        if self.current_file_path in self.symbol_table.unprocessed_files:
            self.symbol_table.unprocessed_files.remove(self.current_file_path)
        else:
            print(f"File {self.current_file_path} already processed")
            return
        for node in file_node.parsed_nodes:
            self._analyze_node_recursive(node)

    def _analyze_node_context_recursive(self, node: BaseSchema):
        if node.node_type == SchemaType.IMPORT:
            imported_modules = self.import_handler.handle_import_node(
                node, self.symbol_table.scope_manager.current_scope.qualified_name, self.current_file_path
            )

            for imported_module in imported_modules:
                file_node = self.symbol_table.file_nodes[imported_module]
                scope = self.symbol_table.scope_manager.get_scope_by_qname(
                    imported_module)
                current_scope = self.symbol_table.scope_manager.current_scope
                self.symbol_table.scope_manager.enter_scope_by_scope_type(
                    scope)
                self.context_analyze_symbols(file_node)

                self.symbol_table.scope_manager.exit_scope()
                self.symbol_table.scope_manager.enter_scope_by_scope(
                    current_scope)

        elif node.node_type == SchemaType.IMPORT_FROM:
            imported_modules = self.import_handler.handle_import_from_node(
                node, self.symbol_table.scope_manager.current_scope.qualified_name, self.current_file_path
            )

            for imported_module in imported_modules:
                file_node = self.symbol_table.file_nodes[imported_module]
                current_scope = self.symbol_table.scope_manager.current_scope
                scope = self.symbol_table.scope_manager.get_scope_by_qname(
                    imported_module)
                self.symbol_table.scope_manager.enter_scope_by_scope(
                    scope)
                self.context_analyze_symbols(file_node)
                self.symbol_table.scope_manager.exit_scope()
                self.symbol_table.scope_manager.enter_scope_by_scope(
                    current_scope)

        elif node.node_type == SchemaType.FUNCTION or node.node_type == SchemaType.CLASS:
            qname = f"{self.symbol_table.scope_manager.current_scope.qualified_name}.{node.name}"
            scope = self.symbol_table.scope_manager.get_scope_by_qname(qname)

            if scope:
                self.symbol_table.scope_manager.enter_scope_by_scope(
                    scope)

                if node.node_type == SchemaType.CLASS:
                    self.class_handler.handle_class_node(node)
                for child in node.children:
                    self._analyze_node_context_recursive(child)

                self.symbol_table.scope_manager.exit_scope()

        elif node.node_type == SchemaType.CALL:
            current_frame = self.symbol_table.scope_manager.call_tracker.current_frame

            if current_frame and current_frame.callee_symbol.qualified_name != self.symbol_table.scope_manager.current_scope.qualified_name:
                return

            self.call_handler.handle_call(node)

        elif node.node_type == SchemaType.ASSIGN or node.node_type == SchemaType.ANN_ASSIGN:

            self.assignment_handler.handle_assign_node(
                node)
