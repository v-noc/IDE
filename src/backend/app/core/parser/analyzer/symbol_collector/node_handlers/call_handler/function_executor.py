from __future__ import annotations
from typing import Callable, Dict, Any, Optional, List

from pydantic import BaseModel
from app.core.parser.scope_manager.core.symbol import Symbol, SymbolType
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.ast.models import (
    ArgSchema,
    BaseSchema,
    KeywordSchema,
    NameSchema,
    AttributeSchema,
)

from .symbol_resolver import ResolutionResult
from app.core.parser.analyzer.symbol_table import SymbolTable


class Args(BaseModel):
    name: str
    type: Optional[str] = None


class FunctionExecutor:
    def __init__(
        self,
        scope_manager: ScopeManager,
        analyzer_callback: Callable[[BaseSchema], None],
        symbol_table: SymbolTable,
    ):
        self.scope_manager = scope_manager
        self.analyzer_callback = analyzer_callback
        # symbol_table gives access to qname_to_node mapping
        self.symbol_table = symbol_table

    def execute(
        self,
        callee_result: ResolutionResult,
        args: List[BaseSchema] | List[Any],
        keywords: List[KeywordSchema],
    ) -> Optional[Symbol]:
        callee_symbol = callee_result.symbol
        if not callee_symbol:
            return None

        callee_symbol = callee_symbol.resolve_final()

        if callee_symbol.symbol_type not in (
            SymbolType.FUNCTION,
            SymbolType.CAPTURED_CLOSURE,
        ):
            return None

        func_node = self.symbol_table.qname_to_function_node.get(
            callee_symbol.qualified_name
        )

        constructed_args: Dict[str, Any] = {}
        if callee_result.instance_context is not None:
            constructed_args["self"] = callee_result.instance_context

        if func_node and getattr(func_node, "args", None):
            func_node_args = []
            for arg in func_node.args:
                arg_name = arg.name
                func_node_args.append(Args(name=arg_name, type=None))

            constructed_args.update(
                self._build_arguments(func_node_args, args, keywords)
            )

        # Start call frame
        self.scope_manager.invoke(
            callee_symbol, constructed_args
        )

        # call_schema = CallSchema(
        #     name=callee_symbol.name,
        #     qname=callee_symbol.qualified_name,
        #     line_no=12,
        # )
        # If we don't have the function node, end the call gracefully
        if not func_node:
            return self.scope_manager.end_current_call(None)

        # Execute function body
        current_scope = self.scope_manager.current_scope
        scope = self.scope_manager.get_scope_by_qname(
            callee_symbol.qualified_name
        )
        if not scope:
            return self.scope_manager.end_current_call(None)

        self.scope_manager.enter_scope_by_scope(scope)
        for child in func_node.children:
            self.analyzer_callback(child)

        return_value = self._resolve_return_value(func_node)

        self.scope_manager.exit_scope()

        resolved_return_value = self.scope_manager.end_current_call(
            return_value
        )
        self.scope_manager.enter_scope_by_scope(current_scope)
        return resolved_return_value

    def instantiate_class(
        self,
        class_symbol: Symbol,
        args: List[BaseSchema] | List[Any],
        keywords: List[KeywordSchema],
    ) -> Optional[Symbol]:
        # Create instance (without running __init__)
        instance_symbol = self.scope_manager.instantiate(class_symbol.name)

        # Resolve __init__ and, if present, call it with instance bound as self
        init_symbol = self.scope_manager.resolve_method(
            instance_symbol.instance_scope.qualified_name,
            "__init__",
        )
        if init_symbol:
            # Execute __init__
            callee_result = ResolutionResult(
                symbol=init_symbol, instance_context=instance_symbol
            )
            self.execute(callee_result, args, keywords)

        return instance_symbol

    def _build_arguments(
        self,
        func_schema: List[Args],
        positional_args: List[BaseSchema] | List[Any],
        keyword_args: List[KeywordSchema],
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        # Gather parameter names in order
        param_names = [
            f.name for f in func_schema
        ]

        # 1) Positional arguments
        for idx, call_arg in enumerate(positional_args or []):
            if idx >= len(param_names):
                break
            param_name = param_names[idx]
            if not param_name:
                continue

            resolved = None
            if isinstance(call_arg, NameSchema):
                resolved = self.scope_manager.resolve_symbol_in_context(
                    call_arg.name
                )
                if resolved:
                    resolved = resolved.resolve_final()
            elif isinstance(call_arg, AttributeSchema):
                # Conservatively skip deep attribute here; higher-level
                # resolver should pass instances
                resolved = None
            else:
                resolved = None

            if resolved is not None:
                result[param_name] = resolved

        # 2) Keyword arguments
        for kw in keyword_args or []:
            kw_name = getattr(kw, "name", None)
            kw_value = getattr(kw, "value", None)
            if not kw_name:
                continue

            resolved_kw = None
            if isinstance(kw_value, NameSchema):
                resolved_kw = self.scope_manager.resolve_symbol_in_context(
                    kw_value.name
                )
                if resolved_kw:
                    resolved_kw = resolved_kw.resolve_final()
            elif isinstance(kw_value, AttributeSchema):
                resolved_kw = None

            if resolved_kw is not None:
                result[kw_name] = resolved_kw

        return result

    def _resolve_return_value(self, func_node) -> Optional[Symbol]:
        if getattr(func_node, "return_values", None):
            first = func_node.return_values[0]
            if isinstance(first, NameSchema):
                sym = self.scope_manager.resolve_symbol_in_context(first.name)
                return sym.resolve_final() if sym else None
        return None
