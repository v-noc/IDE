import os
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import ClassSchema, FunctionSchema
from app.core.model.properties import CodePosition
from app.core.model.nodes import ClassNode
from app.core.parser.scope_manager.core.scope import ScopeType
from app.core.parser.analyzer.symbol_collector.node_handlers.function_handler \
    import FunctionHandler
from app.core.parser.ast.node_tracking import add_comment
from app.core.watcher.service import get_watcher_service


class ClassHandler:
    """Handles class-related nodes"""

    def __init__(
        self,
        symbol_table: SymbolTable,
        function_handler: FunctionHandler,
    ):
        self.symbol_table = symbol_table
        self.function_handler = function_handler
        self.watcher_service = get_watcher_service()

    def handle_inherit_class_node(self, node: ClassSchema):
        """Process a class node and set up inheritance"""
        print(f"Processing class node: {node.name}")

        # Register class schema
        # Shortcuts
        qname = self.symbol_table.scope_manager.current_scope.qualified_name
        class_service = self.symbol_table.node_service["class"]
        class_node: ClassNode = class_service.get_by_qname(qname)

        if class_node is None:
            return

        scope_manager = self.symbol_table.scope_manager

        classes = []
        for implemented_base in node.implements:
            resolved_base_qname = scope_manager.resolve_symbol_in_context(
                implemented_base.name
            )
            if not resolved_base_qname:
                continue
            classes.append(resolved_base_qname.resolve_final().qualified_name)

        scope_manager.register_class(classes)

        # Populate inherited members
        scope_manager.calculate_all_mro()
        mro = scope_manager.get_mro(qname)
        init_symbol = scope_manager.resolve_method(qname, "__init__")
        if init_symbol is None:
            scope_manager.enter_scope("__init__", ScopeType.FUNCTION)
            function_schema = FunctionSchema(
                name="__init__", args=[], position=node.position
            )
            self.function_handler.handle_function_node(function_schema)
            scope_manager.exit_scope()

        class_node.implements = mro
        class_service.update(class_node)

    def handle_class_node(self, node: ClassSchema):
        """Process a class node and set up inheritance"""
        print(f"Processing class node: {node.name}")

        # Register class schema
        qname = self.symbol_table.scope_manager.current_scope.qualified_name
        parent_qname = (
            self.symbol_table.scope_manager.current_scope.parent.qualified_name
        )
        parent_node = self.symbol_table.qname_to_node[parent_qname]
        class_service = self.symbol_table.node_service["class"]
        class_name = node.name

        # Resolve absolute path and current line-shift for the file
        abs_path = None
        prior_inserts = 0
        try:
            scope = self.symbol_table.scope_manager.current_scope
            while scope.parent and scope.scope_type != ScopeType.MODULE:
                scope = scope.parent
            module_qname = scope.qualified_name
            file_container = self.symbol_table.file_containers.get(
                module_qname
            )
            if file_container:
                project_root = self.symbol_table.project_node.path
                file_path = file_container.file_path
                abs_path = (
                    file_path
                    if os.path.isabs(file_path)
                    else os.path.normpath(
                        os.path.join(project_root, file_path)
                    )
                )
                prior_inserts = (
                    self.symbol_table.file_path_to_line_inserts.get(
                        abs_path, 0
                    )
                )
        except Exception:
            pass

        adjusted_start = node.position.line_no + prior_inserts
        adjusted_end = (
            node.position.end_line_no + prior_inserts
            if node.position.end_line_no is not None
            else None
        )
        code_position = CodePosition(
            line_no=adjusted_start,
            col_offset=node.position.col_offset,
            end_line_no=adjusted_end,
            end_col_offset=node.position.end_col_offset,
        )

        class_node = None
        if node.id:
            try:
                fetched = class_service.get(node.id)
                # Guard: ensure the fetched node is truly a class
                if fetched and getattr(fetched, "node_type", None) == "class":
                    class_node = fetched
                    class_node.position = code_position
                    class_service.update(class_node)
                else:
                    class_node = None
            except Exception:
                # If the stored ID is wrong or points to a different type, ignore it
                class_node = None

        if class_node is None:
            class_node = class_service.create(
                name=class_name,
                qname=qname,
                description=f"{class_name} class",
                position=code_position
            )
            parent_service = self.symbol_table.node_service[
                parent_node.node_type
            ]
            parent_service.add_class(parent_node.id, class_node.id)

            # Persist the created class id back into source as a comment
            try:
                # Ascend to module scope
                scope = self.symbol_table.scope_manager.current_scope
                while scope.parent and scope.scope_type != ScopeType.MODULE:
                    scope = scope.parent
                module_qname = scope.qualified_name
                if abs_path:
                    adjusted_line = node.position.line_no + prior_inserts
                    result = add_comment(
                        filepath=abs_path,
                        target_name=node.name,
                        comment_text=f"ID: {class_node.id}",
                        line_number=adjusted_line,
                        position="above",
                    )
                    if result.get("success"):
                        added = result.get("added_lines", 0)
                        if added:
                            self.symbol_table.file_path_to_line_inserts[
                                abs_path
                            ] = prior_inserts + added
                            class_node.position.line_no = (
                                class_node.position.line_no + added
                            )
                            if class_node.position.end_line_no is not None:
                                class_node.position.end_line_no = (
                                    class_node.position.end_line_no + added
                                )
                            class_service.update(class_node)
            except Exception:
                # Best-effort; failures here should not break analysis
                pass

        print(f"Class node: {class_node}")
        self.symbol_table.qname_to_node[qname] = class_node
