# app/core/parser/scope_manager/storage/symbol_table.py

from typing import Optional, TYPE_CHECKING, Dict
from sqlalchemy.orm import Session
from sqlalchemy import delete, insert
from .database import DatabaseManager
from .models import ScopeORM, SymbolORM, wildcard_imports


class SymbolTable:
    """
    Storage manager for scopes and symbols, now backed by SQLite.
    API remains compatible with the prior RocksDict-based implementation.
    """

    # Multiton: one SymbolTable per db_name
    _instances: Dict[str, "SymbolTable"] = {}

    def __new__(cls, db_name: str = "scope_manager"):
        if db_name not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            instance._db_name = db_name
            instance._session = None
            instance._initialize(db_name)
            cls._instances[db_name] = instance
        return cls._instances[db_name]

    def _initialize(self, db_name: str):
        """Initialize the database connection."""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.db_manager = DatabaseManager(db_name)
        self._session: Optional[Session] = None
        self._initialized = True

    @property
    def session(self) -> Session:
        """Get or create a database session."""
        if self._session is None or not self._session.is_active:
            self._session = self.db_manager.get_session()
        return self._session

    # --- Scope Methods ---

    def get_scope(self, scope_id: str) -> Optional["Scope"]:
        """Retrieve a scope by its ID (qualified name)."""
        scope_orm = self.session.query(ScopeORM).filter(
            ScopeORM.id == scope_id
        ).first()

        if scope_orm:
            return ScopeAdapter.from_orm(scope_orm)
        return None

    def save_scope(self, scope: "Scope"):
        """Save or update a scope."""
        # Check if it exists
        existing = self.session.query(ScopeORM).filter(
            ScopeORM.id == scope.id
        ).first()

        if existing:
            # Update existing
            existing.name = scope.name
            existing.scope_type = scope.scope_type.value
            existing.parent_id = scope.parent_id
            # Sync wildcard imports association with order and no duplicates
            self._sync_wildcard_imports(scope)
        else:
            # Create new
            scope_orm = ScopeAdapter.to_orm(scope)
            self.session.add(scope_orm)
            self.session.flush()
            # Sync wildcard imports association for new scope
            self._sync_wildcard_imports(scope)

        self.session.commit()

    def delete_scope(self, scope_id: str):
        """Delete a scope and all its children (cascade)."""
        scope_orm = self.session.query(ScopeORM).filter(
            ScopeORM.id == scope_id
        ).first()

        if scope_orm:
            self.session.delete(scope_orm)
            self.session.commit()

    # --- Symbol Methods ---

    def get_symbol(self, symbol_id: str) -> Optional["Symbol"]:
        """Retrieve a symbol by its ID (qualified name)."""
        symbol_orm = self.session.query(SymbolORM).filter(
            SymbolORM.id == symbol_id
        ).first()

        if symbol_orm:
            return SymbolAdapter.from_orm(symbol_orm)
        return None

    def save_symbol(self, symbol: "Symbol"):
        """Save or update a symbol."""
        existing = self.session.query(SymbolORM).filter(
            SymbolORM.id == symbol.id
        ).first()

        if existing:
            # Update existing
            existing.name = symbol.name
            existing.symbol_type = symbol.symbol_type.value
            existing.defining_scope_id = symbol.defining_scope_id
            existing.assigned_to_id = symbol.assigned_to_id
            existing.instance_scope_id = symbol.instance_scope_id

            existing.metadata_json = symbol.metadata
        else:
            # Create new
            symbol_orm = SymbolAdapter.to_orm(symbol)
            self.session.add(symbol_orm)

        self.session.commit()

    def delete_symbol(self, symbol_id: str):
        """Delete a symbol."""
        symbol_orm = self.session.query(SymbolORM).filter(
            SymbolORM.id == symbol_id
        ).first()

        if symbol_orm:
            self.session.delete(symbol_orm)
            self.session.commit()

    # --- Advanced Query Methods (New Capabilities) ---

    def get_symbols_by_scope(self, scope_id: str) -> list["Symbol"]:
        """Get all symbols in a scope efficiently (single query)."""
        symbol_orms = self.session.query(SymbolORM).filter(
            SymbolORM.defining_scope_id == scope_id, SymbolORM.is_runtime == False
        ).all()

        return [SymbolAdapter.from_orm(s) for s in symbol_orms]

    def find_symbols_by_name(self, name: str) -> list["Symbol"]:
        """Find all symbols with a specific name across all scopes."""
        symbol_orms = self.session.query(SymbolORM).filter(
            SymbolORM.name == name, SymbolORM.is_runtime == False
        ).all()

        return [SymbolAdapter.from_orm(s) for s in symbol_orms]

    def get_child_scopes(self, parent_id: str) -> list["Scope"]:
        """Get all child scopes of a parent (single query)."""
        scope_orms = self.session.query(ScopeORM).filter(
            ScopeORM.parent_id == parent_id
        ).all()

        return [ScopeAdapter.from_orm(s) for s in scope_orms]

    def close(self):
        """Close the database session."""
        if self._session:
            self._session.close()
            self._session = None

    # --- Internal helpers ---

    def _sync_wildcard_imports(self, scope: "Scope") -> None:
        """Synchronize the wildcard import association table for a scope.
        Ensures insertion order is preserved and duplicates are removed
        with last-occurrence winning semantics.
        """
        # Deduplicate preserving the last occurrence order
        ids = scope.wildcard_import_scope_ids
        dedup_reversed = []
        seen = set()
        for sid in reversed(ids):
            if sid in seen:
                continue
            seen.add(sid)
            dedup_reversed.append(sid)
        desired_ids = list(reversed(dedup_reversed))

        # Clear existing associations
        self.session.execute(
            delete(wildcard_imports).where(
                wildcard_imports.c.scope_id == scope.id
            )
        )

        # Insert back in required order with import_order metadata
        for order_index, imported_id in enumerate(desired_ids):
            self.session.execute(
                insert(wildcard_imports).values(
                    scope_id=scope.id,
                    imported_scope_id=imported_id,
                    import_order=order_index,
                )
            )
