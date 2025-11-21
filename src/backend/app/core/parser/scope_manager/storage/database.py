# app/core/parser/scope_manager/storage/database.py

import os
from typing import Dict
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
import platformdirs as pl


def get_db_url(db_name: str) -> str:
    """Generate SQLite database URL."""
    db_dir = os.path.join(pl.user_data_dir("v-noc"), "scope_manager")
    os.makedirs(db_dir, exist_ok=True)
    if db_name == "memory":
        return "sqlite:///:memory:"
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

    @classmethod
    def reset_instance(cls, db_name: str):
        """Reset the database instance (useful for testing)."""
        if db_name in cls._instances:
            instance = cls._instances[db_name]
            if instance._engine:
                instance._engine.dispose()
            del cls._instances[db_name]

    def _initialize(self, db_name: str):
        """Initialize the database engine and session factory."""
        db_url = get_db_url(db_name)
        print(f"db_url: {db_url}")
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

    @property
    def engine(self):
        return self._engine
