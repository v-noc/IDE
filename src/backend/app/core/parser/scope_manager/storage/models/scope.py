from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Index, JSON, Table
from sqlalchemy.orm import relationship
from ..database import Base


class ScopeType(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    PACKAGE = "package"


class ScopeChangeType(str, Enum):
    """Types of changes that can occur in a scope"""
    UNCHANGED = "unchanged"
    DOCSTRING_CHANGED = "docstring_changed"
    BODY_CHANGED = "body_changed"
    SIGNATURE_CHANGED = "signature_changed"


scope_inheritance = Table(
    'scope_inheritance',
    Base.metadata,
    Column('child_id', String, ForeignKey('scopes.id'), primary_key=True),
    Column('parent_id', String, ForeignKey('scopes.id'), primary_key=True)
)


class ScopeModel(Base):
    __tablename__ = 'scopes'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    # 'module', 'class', 'function', 'execution'
    scope_type = Column(String, nullable=False, index=True)

    is_root = Column(Boolean, default=False, index=True)

    # The Adjacency List link: connects a scope to its parent.
    parent_id = Column(String, ForeignKey(
        'scopes.id', ondelete='CASCADE'), index=True)

    # For incremental analysis: stores the hash of the source file.
    source_unit_id = Column(String, ForeignKey(
        'source_unit.id', ondelete='CASCADE'), index=True)

    # --- Staleness Tracking for Resync ---
    is_stale = Column(Boolean, default=False, index=True)
    stale_reason = Column(String, nullable=True)
    stale_since = Column(String, nullable=True)  # ISO datetime string
    last_verified = Column(String, nullable=True)  # ISO datetime string

    # For Classes: track base classes via a relationship instead of JSON
    base_classes_ids = relationship(
        "ScopeModel",
        secondary="scope_inheritance",
        primaryjoin="ScopeModel.id==scope_inheritance.c.child_id",
        secondaryjoin="ScopeModel.id==scope_inheritance.c.parent_id",
        backref="derived_classes"
    )

    # SQLAlchemy relationships for navigation
    parent = relationship(
        "ScopeModel",
        remote_side=[id],
        back_populates="children",
    )
    children = relationship(
        "ScopeModel", back_populates="parent", cascade="all, delete-orphan")
    symbols = relationship(
        "SymbolModel",
        back_populates="defining_scope",
        cascade="all, delete-orphan",
        foreign_keys="SymbolModel.defining_scope_id",
    )

    symbol = relationship(
        "SymbolModel",
        back_populates="defines_scope",
        uselist=False,
        foreign_keys="SymbolModel.defines_scope_id"
    )

    source_unit = relationship(
        "SourceUnit",
        back_populates="scope",
        uselist=False,
        foreign_keys=[source_unit_id]
    )


class SourceUnit(Base):
    """Represents a physical file. Key for Resync logic."""
    __tablename__ = "source_unit"
    id = Column(String, primary_key=True)
    file_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    last_analyzed = Column(String, nullable=True)  # ISO datetime string

    scope = relationship(
        "ScopeModel",
        back_populates="source_unit",
        uselist=False
    )


class DependencyEdge(Base):
    """Tracks file-to-file dependency relationships for Resync logic."""
    __tablename__ = "dependency_edges"

    id = Column(String, primary_key=True)

    # If File A imports File B, A is the source and B is the target.
    source_file_id = Column(
        String,
        ForeignKey("source_unit.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_file_id = Column(
        String,
        ForeignKey("source_unit.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 'direct', 'wildcard', etc.
    import_type = Column(String, nullable=False)
