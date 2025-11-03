from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional

from app.core.parser.scope_manager.core.symbol import Symbol, SymbolType
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.ast.models import (
    AttributeSchema,
    BaseSchema,
    CallSchema,
    NameSchema,
)
from pydantic import BaseModel


class ResolutionResult(BaseModel):
    symbol: Optional[Symbol] = None
    instance_context: Optional[Symbol] = None


class SymbolResolver:
    def __init__(self, scope_manager: ScopeManager):
        self.scope_manager = scope_manager
        self.call_handler_callback: Optional[
            Callable[[CallSchema], Optional[Symbol]]
        ] = None

    def resolve_expression(self, node: BaseSchema) -> ResolutionResult:
        if isinstance(node, NameSchema):
            return self._resolve_name(node)

        if isinstance(node, AttributeSchema):
            return self._resolve_attribute(node)

        if isinstance(node, CallSchema):
            if self.call_handler_callback is None:
                return ResolutionResult()
            sym = self.call_handler_callback(node)
            return ResolutionResult(symbol=sym)

        return ResolutionResult()

    # --- Internals ---
    def _resolve_name(self, node: NameSchema) -> ResolutionResult:
        sym = self.scope_manager.resolve_symbol_in_context(node.name)
        if not sym:
            return ResolutionResult()

        sym_final = sym.resolve_final()
        if not sym_final:
            return ResolutionResult()

        # If "self" parameter is visible, expose it as instance context
        if sym_final.name == "self" and sym_final.symbol_type in (
            SymbolType.PARAMETER,
            SymbolType.OBJECT_INSTANCE,
        ):
            # If parameter, try to get/create an instance for
            # context-sensitive attribute/method resolution
            if (
                sym_final.symbol_type == SymbolType.PARAMETER
                and sym_final.defining_scope
                and sym_final.defining_scope.parent
            ):
                try:
                    instance_obj = self.scope_manager.instantiate(
                        sym_final.defining_scope.parent.name
                    )
                    return ResolutionResult(
                        symbol=instance_obj, instance_context=instance_obj
                    )
                except Exception as e:
                    return ResolutionResult(symbol=sym)
            return ResolutionResult(
                symbol=sym,
                instance_context=(
                    sym_final
                    if sym_final.symbol_type == SymbolType.OBJECT_INSTANCE
                    else None
                ),
            )

        return ResolutionResult(symbol=sym)

    def _resolve_attribute(self, node: AttributeSchema) -> ResolutionResult:
        # Handle super() before any base resolution attempts
        super_result = self._resolve_super_attribute(node)
        if super_result is not None and super_result.symbol is not None:
            return super_result

        base_result = (
            self.resolve_expression(node.value) if node.value else ResolutionResult()
        )
        if not base_result.symbol:
            return ResolutionResult()

        base_symbol = base_result.symbol.resolve_final()
        attr_name = node.name

        # Instance: prefer methods via method resolver,
        # then instance/class attrs
        if base_symbol.symbol_type == SymbolType.OBJECT_INSTANCE:
            inst_scope = base_symbol.instance_scope
            if inst_scope is not None:
                # Try method on instance via class scope qname
                method_sym = self.scope_manager.resolve_method(
                    inst_scope.qualified_name, attr_name
                )
                if method_sym:
                    return ResolutionResult(
                        symbol=method_sym, instance_context=base_symbol
                    )
                # Fallback to attributes on instance/class scope
                if attr_name in inst_scope.symbols:
                    return ResolutionResult(
                        symbol=inst_scope.symbols[attr_name],
                        instance_context=base_symbol,
                    )
                if inst_scope.parent and (attr_name in inst_scope.parent.symbols):
                    return ResolutionResult(
                        symbol=inst_scope.parent.symbols[attr_name],
                        instance_context=base_symbol,
                    )

        # Class attribute or method
        if base_symbol.symbol_type == SymbolType.CLASS:
            class_scope = self.scope_manager.get_scope_by_qname(
                base_symbol.qualified_name
            )
            if class_scope and attr_name in class_scope.symbols:
                return ResolutionResult(symbol=class_scope.symbols[attr_name])

        # Module attribute
        if base_symbol.symbol_type == SymbolType.MODULE:
            module_scope = self.scope_manager.get_scope_by_qname(
                base_symbol.qualified_name
            )
            if module_scope and attr_name in module_scope.symbols:
                return ResolutionResult(symbol=module_scope.symbols[attr_name])

        # Import indirection: resolve target and retry by name
        if base_symbol.symbol_type == SymbolType.IMPORT:
            target = base_symbol.resolve_final()
            if target is not base_symbol:
                # Retry with a synthetic name access on the resolved target
                return self._resolve_attribute(
                    AttributeSchema(
                        node_type=node.node_type,
                        position=node.position,
                        name=attr_name,
                        value=NameSchema(
                            node_type=node.node_type,
                            position=node.position,
                            name=target.name,
                        ),
                    )
                )

        # Fallback: attributes on defining scope of symbol objects
        if (
            base_symbol.defining_scope
            and attr_name in base_symbol.defining_scope.symbols
        ):
            return ResolutionResult(
                symbol=base_symbol.defining_scope.symbols[attr_name],
                instance_context=base_result.instance_context,
            )

        return ResolutionResult()

    def _resolve_super_attribute(
        self, node: AttributeSchema
    ) -> Optional[ResolutionResult]:
        # Detect super access patterns: super.attr or super().attr
        is_super_value = False
        if isinstance(node.value, NameSchema) and node.value.name == "super":
            is_super_value = True
        elif isinstance(node.value, CallSchema):
            func_node = node.value.func
            if isinstance(func_node, NameSchema) and func_node.name == "super":
                is_super_value = True

        if not is_super_value:
            return None

        # Derive instance context from self if possible
        instance_symbol = None
        parent_self = self.scope_manager.resolve_symbol_in_context("self")
        if parent_self:
            if parent_self.resolve_final():
                parent_self = parent_self.resolve_final()
            if (
                parent_self.symbol_type == SymbolType.PARAMETER
                and parent_self.defining_scope
                and parent_self.defining_scope.parent
            ):
                try:
                    instance_symbol = self.scope_manager.instantiate(
                        parent_self.defining_scope.parent.name
                    )
                except Exception:
                    instance_symbol = None
            elif parent_self.symbol_type == SymbolType.OBJECT_INSTANCE:
                instance_symbol = parent_self

        # Ask scope manager to resolve super according to MRO
        method_scope = self.scope_manager.current_scope
        super_sym = None
        if method_scope is not None:
            try:
                super_sym = self.scope_manager.resolve_super_call(
                    method_scope, node.name
                )
            except Exception:
                super_sym = None

        if super_sym is None:
            return ResolutionResult()

        return ResolutionResult(
            symbol=super_sym,
            instance_context=instance_symbol,
        )
