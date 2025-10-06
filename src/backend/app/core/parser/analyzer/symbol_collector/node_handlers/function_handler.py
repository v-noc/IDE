import os
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import FunctionSchema
from app.core.parser.scope_manager.core.symbol import SymbolType
from app.core.model.properties import CodePosition
from app.core.parser.scope_manager.core.scope import ScopeType
from app.core.parser.ast.node_tracking import add_comment


class FunctionHandler:
    """Handles function-related nodes"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def handle_function_node(self, node: FunctionSchema):
        """Register function schema and define argument symbols with
        resolved types.
        """
        current_scope = (
            self.symbol_table.scope_manager.current_scope.qualified_name
        )
        name_node = node.name
        parent_qname = (
            self.symbol_table.scope_manager.current_scope.parent
            .qualified_name
        )
        parent_node = self.symbol_table.qname_to_node[parent_qname]

        function_service = self.symbol_table.node_service['function']

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

        # Build code position adjusted by any prior inserted comment lines
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
        function_node = None
        if node.id:
            function_node = function_service.get(node.id)

            if function_node:
                function_node.position = code_position
                function_service.update(function_node)

        if function_node is None:
            function_node = function_service.create(
                name=name_node,
                qname=current_scope,
                description=f"{name_node} function",
                position=code_position
            )

            parent_service = self.symbol_table.node_service[
                parent_node.node_type
            ]
            parent_service.add_function(parent_node.id, function_node.id)

            # Persist the created function id back into source as a comment
            try:
                if abs_path:
                    adjusted_line = node.position.line_no + prior_inserts
                    result = add_comment(
                        filepath=abs_path,
                        target_name=node.name,
                        comment_text=f"ID: {function_node.id}",
                        line_number=adjusted_line,
                        position="above",
                    )
                    if result.get("success"):
                        added = result.get("added_lines", 0)
                        if added:
                            self.symbol_table.file_path_to_line_inserts[
                                abs_path
                            ] = prior_inserts + added
                            # Update stored position to reflect the
                            # inserted line
                            function_node.position.line_no = (
                                function_node.position.line_no + added
                            )
                            if function_node.position.end_line_no is not None:
                                function_node.position.end_line_no = (
                                    function_node.position.end_line_no + added
                                )
                            function_service.update(function_node)
            except Exception:
                # Best-effort; failures here should not break analysis
                pass

        self.symbol_table.qname_to_node[current_scope] = function_node

        # Define argument symbols with resolved types
        for arg in node.args:
            arg_name = arg.name

            self.symbol_table.scope_manager.define_symbol(
                arg_name,
                SymbolType.PARAMETER,
            )

        self.symbol_table.qname_to_function_node[current_scope] = node
