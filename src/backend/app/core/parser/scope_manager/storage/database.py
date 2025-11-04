# app/core/parser/scope_manager/storage/database.py

import os
from typing import Optional, TYPE_CHECKING, List, Dict
from sqlalchemy import create_engine, event, and_
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
import platformdirs as pl


if TYPE_CHECKING:
    from app.core.parser.scope_manager.storage.models import SymbolORM
    from app.core.parser.scope_manager.storage.models import ScopeORM
    from app.core.parser.scope_manager.core.symbol import Symbol
    from app.core.parser.scope_manager.core.scope import Scope


def get_db_url(db_name: str) -> str:
    """Generate SQLite database URL."""
    db_dir = os.path.join(pl.user_data_dir("v-noc"), "scope_manager")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, f"{db_name}.db")
    print(f"Database path: {db_path}")
    return f"sqlite:///{db_path}"


# Base class for all ORM models
Base = declarative_base()


class DatabaseManager:
    """Manages SQLAlchemy engine and sessions."""

    # Multiton: one instance per db_name
    _instances: Dict[str, "DatabaseManager"] = {}

    def __new__(cls, db_name: str = "scope_manager"):
        if db_name not in cls._instances:
            instance = super().__new__(cls)
            # Bind instance-specific attributes
            instance._db_name = db_name
            instance._engine = None
            instance._session_factory = None
            instance._initialize(db_name)
            cls._instances[db_name] = instance
        return cls._instances[db_name]

    def _initialize(self, db_name: str):
        """Initialize the database engine and session factory."""
        db_url = get_db_url(db_name)

        # SQLite-specific optimizations
        self._engine = create_engine(
            db_url,
            echo=False,  # Set to True for SQL debugging
            # Use StaticPool for better performance in single-threaded apps
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,  # Allow multi-threaded access
            }
        )

        # Enable foreign key constraints (disabled by default in SQLite)
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # Better concurrency
            cursor.close()

        # Create session factory
        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )

        # Create all tables
        Base.metadata.create_all(bind=self._engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def get_symbols_by_scope(self, scope_id: str) -> List["Symbol"]:
        """
        Get all symbols defined in a scope.
        This is ONE query instead of N queries.
        """
        from .adapters import SymbolAdapter

        symbol_orms = self.session.query(SymbolORM).filter(
            SymbolORM.defining_scope_id == scope_id
        ).all()

        return [SymbolAdapter.from_orm(s) for s in symbol_orms]

    def get_child_scopes(self, parent_id: str) -> List["Scope"]:
        """
        Get all child scopes of a parent.
        Single query with proper indexing.
        """
        from .adapters import ScopeAdapter

        scope_orms = self.session.query(ScopeORM).filter(
            ScopeORM.parent_id == parent_id
        ).all()

        return [ScopeAdapter.from_orm(s) for s in scope_orms]

    def resolve_symbol_chain(
        self,
        symbol_id: str,
        max_depth: int = 100
    ) -> Optional["Symbol"]:
        """
        Efficiently resolve an assignment chain using a single recursive query.
        This is much faster than calling resolve_final() with multiple round
        trips.
        """
        from .adapters import SymbolAdapter

        # Start with the initial symbol
        current_id = symbol_id
        visited = set()

        for _ in range(max_depth):
            if current_id in visited:
                raise RecursionError(
                    f"Circular assignment detected at {current_id}")
            visited.add(current_id)

            symbol_orm = self.session.query(SymbolORM).filter(
                SymbolORM.id == current_id
            ).first()

            if not symbol_orm:
                return None

            # If it's a function or class, we're done
            if symbol_orm.symbol_type in ('function', 'class'):
                return SymbolAdapter.from_orm(symbol_orm)

            # Follow the assignment
            if symbol_orm.assigned_to_id:
                current_id = symbol_orm.assigned_to_id
            else:
                return SymbolAdapter.from_orm(symbol_orm)

        raise RecursionError(f"Max resolution depth exceeded for {symbol_id}")

    def get_symbols_by_name_in_scope_chain(
        self,
        name: str,
        start_scope_id: str
    ) -> Optional["Symbol"]:
        """
        Walk up the scope chain looking for a symbol by name.
        This implements the LEGB rule efficiently.
        """
        from .adapters import SymbolAdapter

        current_scope_id = start_scope_id
        visited = set()

        while current_scope_id and current_scope_id not in visited:
            visited.add(current_scope_id)

            # Check symbols in current scope
            symbol_orm = self.session.query(SymbolORM).filter(
                and_(
                    SymbolORM.defining_scope_id == current_scope_id,
                    SymbolORM.name == name
                )
            ).first()

            if symbol_orm:
                return SymbolAdapter.from_orm(symbol_orm)

            # Get parent scope
            scope_orm = self.session.query(ScopeORM).filter(
                ScopeORM.id == current_scope_id
            ).first()

            if not scope_orm or not scope_orm.parent_id:
                break

            current_scope_id = scope_orm.parent_id

        return None

    @property
    def engine(self):
        return self._engine
