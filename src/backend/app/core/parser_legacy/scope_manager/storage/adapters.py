# app/core/parser/scope_manager/storage/adapters.py

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.scope import Scope
    from ..core.symbol import Symbol, SymbolType

from .models import ScopeORM, SymbolORM


class ScopeAdapter:
    """Converts between Pydantic Scope and SQLAlchemy ScopeORM."""

    @staticmethod
    def to_orm(scope: "Scope") -> ScopeORM:
        """Convert Pydantic Scope to ORM model."""
        return ScopeORM(
            id=scope.id,
            name=scope.name,
            scope_type=scope.scope_type.value,
            parent_id=scope.parent_id
        )

    @staticmethod
    def from_orm(scope_orm: ScopeORM) -> "Scope":
        from ..core.scope import Scope, ScopeType
        """Convert ORM model to Pydantic Scope."""
        # Build the dictionaries for child and symbol IDs
        child_scope_ids = [
            child.id for child in scope_orm.children]
        symbol_ids = [symbol.id for symbol in scope_orm.symbols]
        wildcard_ids = [ws.id for ws in scope_orm.wildcard_imported_scopes]

        return Scope(
            id=scope_orm.id,
            name=scope_orm.name,
            scope_type=ScopeType(scope_orm.scope_type),
            parent_id=scope_orm.parent_id,
            child_scope_ids=child_scope_ids,
            symbol_ids=symbol_ids,
            wildcard_import_scope_ids=wildcard_ids
        )


class SymbolAdapter:
    """Converts between Pydantic Symbol and SQLAlchemy SymbolORM."""

    @staticmethod
    def to_orm(symbol: "Symbol") -> SymbolORM:
        """Convert Pydantic Symbol to ORM model."""
        return SymbolORM(
            id=symbol.id,
            name=symbol.name,
            symbol_type=symbol.symbol_type.value,
            defining_scope_id=symbol.defining_scope_id,
            assigned_to_id=symbol.assigned_to_id,
            instance_scope_id=symbol.instance_scope_id,
            metadata_json=symbol.metadata,
            is_runtime=symbol.is_runtime
        )

    @staticmethod
    def from_orm(symbol_orm: SymbolORM) -> "Symbol":
        """Convert ORM model to Pydantic Symbol."""
        from ..core.symbol import Symbol, SymbolType
        return Symbol(
            id=symbol_orm.id,
            name=symbol_orm.name,
            symbol_type=SymbolType(symbol_orm.symbol_type),
            defining_scope_id=symbol_orm.defining_scope_id,
            assigned_to_id=symbol_orm.assigned_to_id,
            instance_scope_id=symbol_orm.instance_scope_id,
            metadata=symbol_orm.metadata_json or {},
            is_runtime=symbol_orm.is_runtime
        )
