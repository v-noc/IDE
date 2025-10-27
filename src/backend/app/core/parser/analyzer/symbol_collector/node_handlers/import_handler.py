from typing import Optional, Tuple
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import ImportFromSchema, ImportSchema
from app.core.parser.scope_manager.core.symbol import SymbolType
from app.core.model.nodes import FolderNode, FileNode
from app.core.parser.scope_manager.core.scope import ScopeType


class ImportHandler:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def handle_import_node(self, node: ImportSchema):
        imported_modules = self.process_import(node)

        return imported_modules

    def process_import(self, node: ImportSchema):
        """Process a import node"""
        local_import_modules = []

        for alias in node.names:
            imported_name = alias.asname if alias.asname else alias.name
            imported_qname = f"{alias.name}"

            if imported_qname in self.symbol_table.qname_to_node:
                imported_symbol = self.symbol_table.scope_manager.define_symbol(
                    imported_name, SymbolType.IMPORT
                )
                node = self.symbol_table.qname_to_node.get(imported_qname)
                if isinstance(node, FileNode):
                    local_import_modules.append(imported_qname)

                scope = self.symbol_table.scope_manager.get_scope_by_qname(
                    imported_qname
                )
                if scope:
                    symbol = scope.parent.symbols[scope.name]
                    if symbol:
                        self.symbol_table.scope_manager.track_static_assignment(
                            imported_symbol, symbol
                        )

            else:
                alias = self.symbol_table.scope_manager.define_symbol(
                    imported_name, SymbolType.IMPORT
                )

        return local_import_modules

    def handle_import_from_node(self, node: ImportFromSchema):
        """Process a import from node"""
        imported_modules = self.process_import_from(node)
        return imported_modules

    def process_import_from(self, node: ImportFromSchema):
        local_import_modules = []
        current_scope = self.symbol_table.scope_manager.current_scope
        parent_file_scope = None

        next_scope = current_scope
        while next_scope:
            if next_scope.scope_type == ScopeType.MODULE:
                parent_file_scope = next_scope
                break
            next_scope = next_scope.parent

        for alias in node.names:
            imported_name = alias.asname if alias.asname else alias.name

            target_qname, module_path = self._compute_from_import_targets(
                alias.name, node, parent_file_scope.qualified_name
            )

            if not target_qname:
                continue

            is_external = self._is_external_module(module_path)

            alias_symbol = None
            # Do not define a literal '*' symbol in the scope; instead register
            # wildcard import
            if imported_name != "*":
                alias_symbol = self.symbol_table.scope_manager.define_symbol(
                    imported_name, SymbolType.IMPORT
                )

            if not is_external:
                scope = self.symbol_table.scope_manager.get_scope_by_qname(module_path)

                if scope:
                    if imported_name == "*":
                        # Register wildcard import on the current scope
                        self.symbol_table.scope_manager.register_wildcard_import(
                            current_scope.qualified_name,
                            module_path,
                        )

                    else:
                        symbol = scope.symbols.get(alias.name)
                        if target_qname == module_path:
                            symbol = scope.parent.symbols.get(scope.name)

                        if symbol and alias_symbol is not None:
                            self.symbol_table.scope_manager.track_static_assignment(
                                alias_symbol, symbol
                            )
                module_node = self.symbol_table.qname_to_node.get(module_path)
                if module_node:
                    if isinstance(module_node, FolderNode):
                        if imported_name == "*":
                            local_import_modules.append(module_path)
                        else:
                            local_import_modules.append(f"{module_path}.{alias.name}")
                    else:
                        local_import_modules.append(module_path)
        return local_import_modules

    def _is_external_module(self, module_path: Optional[str]) -> bool:
        if module_path is None:
            return True
        return module_path not in self.symbol_table.qname_to_node

    def _compute_from_import_targets(
        self,
        alias_name: str,
        node: ImportFromSchema,
        file_scope: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return (target_qname, module_path) for a from-import alias."""
        target_qname: Optional[str] = None
        module_path: Optional[str] = None

        if alias_name == "*":
            module_path = self._resolve_module_path(node, file_scope)
            if module_path:
                target_qname = module_path
            return target_qname, module_path

        if node.level > 0:
            if node.module_name is None:
                # from . import utils as u (module import)
                target_qname = self._resolve_relative_module_import(
                    alias_name, node.level, file_scope
                )
                module_path = target_qname
            else:
                module_path = self._resolve_module_path(node, file_scope)
                if module_path:
                    target_qname = f"{module_path}.{alias_name}"

            return target_qname, module_path

        # Absolute import
        if node.module_name:
            target_qname = f"{node.module_name}.{alias_name}"
            module_path = node.module_name
        else:
            target_qname = alias_name
            module_path = target_qname
        return f"{target_qname}", f"{module_path}"

    def _resolve_relative_module_import(
        self, module_name: str, level: int, file_scope: str
    ) -> Optional[str]:
        """Resolve a relative module import."""
        current_parts = file_scope.split(".")

        if level > len(current_parts):
            return None

        base_parts = current_parts[:-level]
        if base_parts:
            target_module = ".".join(base_parts + [module_name])
        else:
            target_module = module_name

        return target_module

    def _resolve_module_path(
        self, node: ImportFromSchema, file_scope: str
    ) -> Optional[str]:
        """Resolve the full module path for from...import"""
        if node.level == 0:
            # Absolute import
            return node.module_name

        if node.module_name is None:
            # This case should be handled by _resolve_relative_module_import
            # But if we get here, handle it
            current_parts = file_scope.split(".")
            if node.level <= len(current_parts):
                if node.level > 0:
                    base_parts = current_parts[: -node.level]
                else:
                    base_parts = current_parts
                return ".".join(base_parts) if base_parts else None
            return None

        # Relative import with module name
        current_parts = file_scope.split(".")

        if node.level > len(current_parts):
            self._log(
                f"  Warning: Relative import level {node.level} exceeds directory depth"
            )
            return None

        # Go up 'level' directories
        if node.level > 0:
            base_parts = current_parts[: -node.level]
        else:
            base_parts = current_parts

        return ".".join(base_parts + [node.module_name])
