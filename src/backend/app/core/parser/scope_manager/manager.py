from typing import Dict, List, Optional, Any


from app.core.parser.scope_manager.class_analysis.mro import MROCalculator
from app.core.parser.scope_manager.class_analysis.method_resolver import MethodResolver
from app.core.parser.scope_manager.class_analysis.model import InheritanceGraph
from app.core.parser.scope_manager.call_context.tracker import CallGraphTracker
from app.core.parser.scope_manager.call_context.resolver import ExecutionContextResolver
from app.core.parser.scope_manager.call_context.instantiation import (
    ClassInstantiationHandler,
)
from app.core.parser.scope_manager.core import SymbolType, Scope, ScopeType, Symbol
from app.core.parser.scope_manager.call_context.models import CallFrame, CallGraph
from app.core.parser.scope_manager.storage.symbol_table import SymbolTable


class ScopeManager:
    """
    Manages the creation and navigation of a scope hierarchy and provides
    class analysis and context-sensitive analysis capabilities.
    """

    def __init__(self, db_name: str = "scope_manager"):
        self.table = SymbolTable(db_name)
        self.current_scope: Optional[Scope] = None
        self.root_scope: Optional[Scope] = None

        self._scope_index: Dict[str, str] = {}

        self._root_symbols: Optional[Symbol] = None

        # --- Class Analysis Components ---
        self.inheritance_graph = InheritanceGraph()
        self.mro_calculator = MROCalculator(self.inheritance_graph)
        self.method_resolver = MethodResolver(self.inheritance_graph, self.table)

        # A map to track what symbol an alias points to.

        # self.current_frame_stack = []

    # Class Analysis Methods

    def register_class(self, base_qnames: List[str]):
        """
        Registers a new class in the inheritance graph.
        """
        if not self.current_scope or self.current_scope.scope_type != ScopeType.CLASS:
            raise TypeError("Can only register a class scope.")

        self.inheritance_graph.add_class(self.current_scope, base_qnames)

    def calculate_all_mro(self):
        """
        Calculates the MRO for all classes in the inheritance graph.
        """
        self.mro_calculator.calculate_all()

    def get_mro(self, class_qname: str) -> List[str]:
        """
        Gets the MRO for a specific class.
        """
        return self.mro_calculator.get_mro(class_qname)

    def resolve_method(self, class_qname: str, method_name: str) -> Optional[Symbol]:
        """
        Resolves a method on a class using its MRO.
        """
        return self.method_resolver.resolve_method(class_qname, method_name)

    def resolve_super_call(
        self, method_scope: Scope, method_name: str
    ) -> Optional[Symbol]:
        """
        Resolves a super().method() call from within a method's scope.
        """

        if not method_scope.parent or method_scope.parent.scope_type != ScopeType.CLASS:
            raise ValueError("super() can only be resolved within a method of a class.")

        class_qname = method_scope.parent.qualified_name
        return self.method_resolver.resolve_super_call(class_qname, method_name)

    # ---

    # Symbol Management Methods

    def add_symbol(self, symbol: Symbol):
        """
        Adds a symbol to the current scope.
        """
        self.current_scope.add_symbol(symbol)

    def track_static_assignment(self, alias: Symbol, target: Symbol):
        """
        Creates a static assignment relationship between symbols.
        This uses the enhanced Symbol assignment tracking.
        """
        alias.assign_to(target)

    def resolve_final_symbol(self, name: str) -> Optional[Symbol]:
        """
        Resolves a symbol by name and follows any alias chains to find the
        final, underlying symbol (e.g., a class or function).
        """
        immediate_symbol = self.lookup_symbol(name)
        if not immediate_symbol:
            return None

        # Use the enhanced symbol resolution
        return immediate_symbol.resolve_final()

    def define_symbol(
        self, name: str, symbol_type: SymbolType, **kwargs: Any
    ) -> Symbol:
        """
        Defines a new symbol in the current scope.
        """
        if not self.current_scope:
            raise ValueError("Cannot define a symbol without an active scope.")

        symbol = Symbol(
            name=name,
            symbol_type=symbol_type,
            defining_scope_id=self.current_scope.id,
            **kwargs,
        )
        symbol.bind_table(self.table)
        self.table.save_symbol(symbol)

        self.current_scope.add_symbol(symbol)
        return symbol

    def define_runtime_variable(
        self, name: str, symbol_type: SymbolType, **kwargs: Any
    ) -> Symbol:
        """
        Defines a new symbol in the CURRENT EXECUTION FRAME's scope.
        This is the correct way to handle local variable assignments during dynamic analysis.
        """
        if not self.call_tracker or not self.call_tracker.current_frame:
            raise RuntimeError(
                "Cannot define a runtime variable without an active call frame."
            )

        # Delegate directly to the current frame's execution scope
        execution_scope = self.call_tracker.current_frame.execution_scope

        symbol = Symbol(
            name=name,
            symbol_type=symbol_type,
            # CRITICAL: Defined in the execution scope
            defining_scope_id=execution_scope.id,
            **kwargs,
        )
        symbol.bind_table(self.table)
        self.table.save_symbol(symbol)

        execution_scope.add_symbol(symbol)
        return symbol

    def lookup_symbol(self, name: str) -> Optional[Symbol]:
        """
        Looks up a symbol by name, starting from the current scope and
        walking up the parent chain according to LEGB rules (Local, Enclosing, Global).

        Note: Built-in scope is not checked here.
        """
        scope = self.table.get_scope(self.current_scope.id)
        scope.bind_table(self.table)
        while scope:
            # Direct symbol in scope
            if name in scope.symbols:
                return scope.symbols[name]

            # Wildcard-imported module scopes (last-import wins)
            for module_scope in reversed(scope.wildcard_import_scopes):
                if name in module_scope.symbols:
                    return module_scope.symbols[name]

            scope = scope.parent

        return None

    # Scope Management Methods

    def create_root_scope(self, name: str = "__main__") -> Scope:
        """
        Creates the root (module-level) scope. This must be the first call.
        """
        if self.root_scope:
            raise ValueError("Root scope has already been created.")

        root = Scope(name=name, scope_type=ScopeType.PROJECT)
        root.bind_table(self.table)
        self._root_symbols = Symbol(
            name=name, symbol_type=SymbolType.PROJECT, defining_scope_id=root.id
        )
        self.table.save_scope(root)
        self._root_symbols.bind_table(self.table)

        self.root_scope = root
        self.current_scope = root
        self._scope_index[name] = root.id

        # --- Initialize Dynamic Analysis Components ---
        # Now that we have a root scope, we can initialize the components.

        self.call_tracker = CallGraphTracker(self)
        self.context_resolver = ExecutionContextResolver(self)
        self.class_instantiator = ClassInstantiationHandler(self, self.table)

        return root

    def enter_scope(self, name: str, scope_type: ScopeType) -> Scope:
        """
        Enters a new nested scope and creates a corresponding symbol
        in the parent scope if necessary (for functions and classes).
        """
        if not self.current_scope:
            raise ValueError(
                "Cannot enter scope without a root. Call create_root_scope() first."
            )

        # --- KEY CHANGE ---
        # Create a symbol in the current scope for the new scope-creating entity.
        if scope_type in (ScopeType.FUNCTION, ScopeType.CLASS, ScopeType.MODULE):
            symbol_type = {
                ScopeType.FUNCTION: SymbolType.FUNCTION,
                ScopeType.CLASS: SymbolType.CLASS,
                ScopeType.MODULE: SymbolType.MODULE,
            }[scope_type]
            # This defines the symbol in the *current* scope, before we descend.
            self.define_symbol(name, symbol_type)
        # --- END KEY CHANGE ---

        new_scope = Scope(name=name, scope_type=scope_type)
        new_scope.bind_table(self.table)
        self.table.save_scope(new_scope)
        self.current_scope.add_child_scope(new_scope)
        self.current_scope = new_scope
        self._scope_index[new_scope.qualified_name] = new_scope.id
        return new_scope

    def exit_scope(self) -> Optional[Scope]:
        """
        Exits the current scope and moves to its parent.
        Returns the scope that was exited.
        """
        if not self.current_scope:
            return None

        exited_scope = self.current_scope
        self.current_scope = self.current_scope.parent
        return exited_scope

    def get_scope_by_qname(self, qualified_name: str) -> Optional[Scope]:
        """
        Retrieves a scope directly by its qualified name.
        """

        scope = self.table.get_scope(self._scope_index.get(qualified_name))
        scope.bind_table(self.table)
        return scope

    def register_wildcard_import(
        self, target_scope_qname: Optional[str], module_qname: str
    ):
        """
        Register that `from module_qname import *` is in effect in `target_scope_qname`.
        If target_scope_qname is None, use the current scope.
        """
        target_scope = (
            self.current_scope
            if target_scope_qname is None
            else self.get_scope_by_qname(target_scope_qname)
        )
        module_scope = self.get_scope_by_qname(module_qname)

        if not target_scope or not module_scope:
            return

        target_scope.add_wildcard_import(module_scope)

    def enter_scope_by_scope(self, scope: Scope) -> Scope:
        """
        Enters a new scope by name.
        """

        if not scope:
            raise ValueError("Please provide a scope")
        self.current_scope = scope
        return scope

    # --- Call Context Methods ---

    def instantiate(self, class_name: str) -> Symbol:
        """
        High-level API to find a class and create an instance of it.
        Note: This does NOT call __init__. Invoke it explicitly if needed.
        """
        class_symbol = self.lookup_symbol(class_name)
        class_symbol_final = class_symbol.resolve_final()

        if class_symbol_final.symbol_type == SymbolType.OBJECT_INSTANCE:
            return class_symbol_final
        # class_symbol = class_symbol.resolve_final()
        if not class_symbol_final or class_symbol_final.symbol_type != SymbolType.CLASS:
            raise NameError(f"Unknown class: {class_name}")

        # The class_instantiator does the work and returns the new instance symbol
        instance_symbol = self.class_instantiator.instantiate_class(class_symbol_final)
        return instance_symbol  # <-- RETURN THE INSTANCE SYMBOL

    def invoke(
        self,
        callee_name: str | Symbol,
        args: Dict[str, Any],
    ) -> CallFrame:
        """
        High-level API to simulate a function call.
        Note: For class instantiation, use the `instantiate()` method.
        """
        callee_symbol = callee_name
        if isinstance(callee_symbol, str):
            callee_symbol = self.lookup_symbol(callee_symbol)
        if not callee_symbol:
            raise NameError(f"Unknown function: {callee_name}")

        if callee_symbol.symbol_type == SymbolType.CLASS:
            raise TypeError(
                f"'{callee_name}' is a class. Use the .instantiate() method to create an object."
            )

        # Now invoke is ONLY for function/method calls
        frame = self.call_tracker.start_call(callee_symbol, args)
        # if len(self.current_frame_stack) == 0:
        #     self.current_scope.children[frame.id] = frame.execution_scope
        # else:
        #     self.current_frame_stack[-1].execution_scope.children[frame.id] = (
        #         frame.execution_scope
        #     )
        # self.current_frame_stack.append(frame)
        return frame

    def resolve_symbol_in_context(self, name: str) -> Optional[Symbol]:
        """
        Context-aware symbol resolution.
        """
        return self.context_resolver.resolve(name)

    def end_current_call(
        self, return_value: Optional[Symbol] = None
    ) -> Optional[Symbol]:
        """
        End the current function call.
        """
        # self.current_frame_stack.pop()
        return self.call_tracker.end_call(return_value)

    def get_call_graph(self) -> CallGraph:
        """
        Get the current call graph.
        """
        return self.call_tracker.call_graph
