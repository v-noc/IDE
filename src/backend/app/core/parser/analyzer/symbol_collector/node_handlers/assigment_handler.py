from typing import Optional

from app.core.parser.analyzer.symbol_collector.node_handlers.call_handler.handler import CallHandler

from app.core.parser.ast.models import AssignSchema, BaseSchema, CallSchema, NameSchema, AttributeSchema
from app.core.parser.analyzer.symbol_collector.node_handlers.call_handler.symbol_resolver import SymbolResolver
from app.core.parser.scope_manager.core.symbol import SymbolType, Symbol
from app.core.parser.analyzer.symbol_table import SymbolTable


class AssigmentHandler:
    def __init__(self, symbol_table: SymbolTable, call_handler: CallHandler):
        """
        Initializes the handler.
        Args:
            symbol_table: The global symbol table.
            call_handler: The shared instance of the CallHandler for
                resolving calls.
        """
        self.symbol_table = symbol_table
        self.scope_manager = symbol_table.scope_manager
        self.resolver = SymbolResolver(self.scope_manager)
        self.call_handler = call_handler

    def handle_assign_node(self, node: AssignSchema):
        """
        Processes an assignment like `x = y` or `obj.attr = func()`.

        Note: The provided AssignNode schema has `value` as a list.
        Standard Python AST has a single value. This assumes a single
        value.
        """

        if not node.value:
            return  # Assignment without a value, e.g., in stubs.

        # Step 1: Resolve the right-hand side (RHS) once to a Symbol.
        value_symbol = self._resolve_value_node_to_symbol(
            node.value[0]
        )

        if not value_symbol:
            # Could not resolve RHS of assignment; ignore.
            return

        # Step 2: Handle all LHS targets (supports `a = b = value`).
        for target_node in node.targets:
            if isinstance(target_node, NameSchema):
                self._handle_name_target(target_node, value_symbol)
            elif isinstance(target_node, AttributeSchema):
                self._handle_attribute_target(target_node, value_symbol)

    def _resolve_value_node_to_symbol(
        self, value_node: BaseSchema
    ) -> Optional[Symbol]:
        """
        Resolves any RHS node to its corresponding Symbol.
       """
        if isinstance(value_node, CallSchema):
            # Delegate entirely to the CallHandler. This is its job.
            return self.call_handler.handle_call(value_node)

        if isinstance(value_node, NameSchema):
            # Find the symbol for the variable being referenced.
            return self.scope_manager.resolve_symbol_in_context(
                value_node.name
            )

        if isinstance(value_node, AttributeSchema):
            # Resolve attribute path via call handler logic.
            return self.resolver._resolve_attribute(
                value_node
            )  # type: ignore[attr-defined]

        # Handle other literal types (int, str, etc.) if you have them.
        return None

    def _handle_name_target(self, target_node: NameSchema, value_symbol: Symbol):
        """
        Handles assignments to simple names, like `x = ...`.
        Defines or re-assigns a variable in the current execution scope.
        """
        var_name = target_node.name

        # Check if the variable already exists in the current context.
        existing_symbol = self.scope_manager.resolve_symbol_in_context(
            var_name
        )

        if existing_symbol:
            # It exists, so we are re-assigning it.
            # We just update what it points to.
            print(f"Re-assigning variable '{var_name}'")
            existing_symbol.assign_to(value_symbol)
        else:
            # It's a new variable definition in this scope.
            print(f"Defining new variable '{var_name}'")
            new_symbol = self.scope_manager.define_symbol(
                var_name, SymbolType.VARIABLE
            )
            print(f"New symbol '{new_symbol.name}'")
            new_symbol.assign_to(value_symbol)

    def _handle_attribute_target(self, target_node: AttributeSchema, value_symbol: Symbol):
        """
        Handles assignments to attributes, like `obj.attr = ...` or
        `a.b.c = ...`.

        Behavior:
        - Resolve the base object of the attribute chain using context-aware
          resolution (names, nested attributes, or calls via the shared
          call handler).
        - If the base resolves to an OBJECT_INSTANCE, define or update the
          attribute in the instance's scope.
        - If the base resolves to a CLASS, define or update the attribute in
          the class scope.
        - If the base resolves to a MODULE, define or update the attribute in
          the module scope.
        - If the base cannot be resolved but we're inside a running frame
          (dynamic execution), fall back to defining a runtime variable for
          the attribute name in the current execution scope to avoid losing
          the assignment.
        """

        # Resolve the left side base of the attribute chain recursively
        def _resolve_attribute_base(node: AttributeSchema) -> Optional[Symbol]:
            base = node.value
            if isinstance(base, NameSchema):
                return self.scope_manager.resolve_symbol_in_context(
                    base.name
                )
            if isinstance(base, AttributeSchema):
                return _resolve_attribute_base(base)
            if isinstance(base, CallSchema):
                return self.call_handler.handle_call(base)
            return None

        base_symbol = _resolve_attribute_base(target_node)
        attr_name = target_node.name

        if base_symbol is None:
            # If base can't resolve but there is a runtime frame, define a
            # runtime variable
            try:
                runtime_sym = self.scope_manager.define_runtime_variable(
                    attr_name,
                    SymbolType.VARIABLE,
                )
                runtime_sym.assign_to(value_symbol)
                return
            except Exception:
                # No active frame; nothing to do safely
                return

        # Work with the final target (follow aliases/imports)
        base_symbol = base_symbol.resolve_final()

        # Instance attribute assignment
        if (
            base_symbol.symbol_type == SymbolType.OBJECT_INSTANCE and
            base_symbol.instance_scope
        ):
            inst_scope = base_symbol.instance_scope
            existing = inst_scope.symbols.get(attr_name)
            if existing:
                existing.assign_to(value_symbol)
            else:
                new_attr = Symbol(
                    name=attr_name,
                    symbol_type=SymbolType.VARIABLE,
                    defining_scope=inst_scope,
                )
                inst_scope.add_symbol(new_attr)
                new_attr.assign_to(value_symbol)
            return

         # Class attribute assignment
        if base_symbol.symbol_type == SymbolType.CLASS:
            class_scope = self.scope_manager.get_scope_by_qname(
                base_symbol.qualified_name
            )
            if not class_scope:
                return
            existing = class_scope.symbols.get(attr_name)
            if existing:
                existing.assign_to(value_symbol)
            else:
                new_attr = Symbol(
                    name=attr_name,
                    symbol_type=SymbolType.VARIABLE,
                    defining_scope=class_scope,
                )
                class_scope.add_symbol(new_attr)
                new_attr.assign_to(value_symbol)
            return

        # Module attribute assignment
        if base_symbol.symbol_type == SymbolType.MODULE:
            module_scope = self.scope_manager.get_scope_by_qname(
                base_symbol.qualified_name
            )
            if not module_scope:
                return
            existing = module_scope.symbols.get(attr_name)
            if existing:
                existing.assign_to(value_symbol)
            else:
                new_attr = Symbol(
                    name=attr_name,
                    symbol_type=SymbolType.VARIABLE,
                    defining_scope=module_scope,
                )
                module_scope.add_symbol(new_attr)
                new_attr.assign_to(value_symbol)
            return

        # Fallback: update the defining scope of the base symbol if available
        defining_scope = (
            base_symbol.defining_scope
            if hasattr(base_symbol, 'defining_scope')
            else None
        )
        if defining_scope is not None:
            existing = defining_scope.symbols.get(attr_name)
            if existing:
                existing.assign_to(value_symbol)
            else:
                new_attr = Symbol(
                    name=attr_name,
                    symbol_type=SymbolType.VARIABLE,
                    defining_scope=defining_scope,
                )
                defining_scope.add_symbol(new_attr)
                new_attr.assign_to(value_symbol)
        # Otherwise do nothing
