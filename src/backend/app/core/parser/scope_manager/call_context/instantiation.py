

from typing import Dict, Any, List
import uuid
from app.core.parser.scope_manager.core.scope import Scope, ScopeType
from app.core.parser.scope_manager.core.symbol import Symbol, SymbolType
from app.core.parser.scope_manager.storage.symbol_table import SymbolTable


class ClassInstantiationHandler:
    """
    Handles class instantiation: MyClass() -> instance.
    Focuses ONLY on creating the instance and its scope.
    """

    def __init__(self, scope_manager: "ScopeManager", table: SymbolTable):
        self.scope_manager = scope_manager
        self.table = table

    def instantiate_class(self, class_symbol: Symbol):
        """
        Create a new object instance following the Object Instantiation Pattern.
        Creates a unique instance_scope and links it to the instance symbol.
        NOTE: This method DOES NOT invoke __init__. Call __init__ explicitly
        using the normal call API if you want to simulate initialization.
        """

        if class_symbol.symbol_type != SymbolType.CLASS:
            raise TypeError(
                f"Cannot instantiate non-class: {class_symbol.name}")

        # 1. Create unique instance scope
        instance_scope = self._create_instance_scope(class_symbol)
        instance_scope.bind_table(self.table)
        self.table.save_scope(instance_scope)
        # 2. Create instance symbol

        instance_symbol = Symbol(
            name=f"{class_symbol.name}",
            symbol_type=SymbolType.OBJECT_INSTANCE,
            defining_scope_id=self.scope_manager.current_scope.id,
            instance_scope_id=instance_scope.id  # CRITICAL: Link symbol to its scope
        )

        instance_symbol.bind_table(self.table)
        self.table.save_symbol(instance_symbol)
        # __init__ is not invoked here. Call it explicitly via the call API.

        return instance_symbol

    def _create_instance_scope(self, class_symbol: Symbol) -> Scope:
        """
        Create a unique instance scope for the object.
        Creates a new Scope of type OBJECT for storing instance attributes,
        linked to the class scope for method lookup as per the Object 
        Instantiation Pattern.
        """

        instance_scope = Scope(
            name=f"{class_symbol.name}",
            scope_type=ScopeType.OBJECT,
            parent_id=class_symbol.defining_scope.id
        )

        instance_scope.bind_table(self.table)
        self.table.save_scope(instance_scope)

        return instance_scope

    def _call_init_method(self, class_symbol: Symbol, instance_symbol: Symbol, init_args: List[Any]):
        """
        Calls the __init__ method on the instance.
        """

        class_scope = self.scope_manager.get_scope_by_qname(
            class_symbol.qualified_name
        )

        init_method = None
        if class_scope:
            init_method = class_scope.symbols.get("__init__")

        # Fallback: resolve __init__ via MRO if not defined directly
        if not init_method:
            init_method = self.scope_manager.method_resolver.resolve_method(
                class_symbol.qualified_name, "__init__"
            )

        if init_method:
            method_args = {"self": instance_symbol, **(init_args or {})}

            self.scope_manager.call_tracker.start_call(
                init_method, method_args, line=0, column=0
            )

            self.scope_manager.call_tracker.end_call(return_value=None)
