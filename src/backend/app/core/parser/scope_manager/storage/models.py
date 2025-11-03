# app/core/parser/scope_manager/storage/models.py

from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

# Many-to-many relationship table for wildcard imports
wildcard_imports = Table(
    'wildcard_imports',
    Base.metadata,
    Column('scope_id', String, ForeignKey(
        'scopes.id', ondelete='CASCADE'), primary_key=True),
    Column('imported_scope_id', String, ForeignKey(
        'scopes.id', ondelete='CASCADE'), primary_key=True),
    Column('import_order', Integer)  # Track order for "last import wins"
)


class ScopeORM(Base):
    """
    SQLAlchemy ORM model for Scope.
    This is the DATABASE representation. Your existing Scope class can be
    converted to/from this model.
    """
    __tablename__ = 'scopes'

    # Primary key - the qualified name
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    scope_type = Column(String, nullable=False, index=True)

    # Hierarchy
    parent_id = Column(String, ForeignKey(
        'scopes.id', ondelete='CASCADE'), nullable=True, index=True)

    # Relationships with lazy loading
    parent = relationship(
        "ScopeORM",
        remote_side=[id],
        back_populates="children",
        lazy="joined"  # Eager load parent in one query
    )

    children = relationship(
        "ScopeORM",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="select"  # Lazy load children
    )

    symbols = relationship(
        "SymbolORM",
        back_populates="defining_scope",
        cascade="all, delete-orphan",
        lazy="select",  # Lazy load symbols
        foreign_keys="SymbolORM.defining_scope_id"
    )

    # Wildcard imports - many-to-many relationship
    wildcard_imported_scopes = relationship(
        "ScopeORM",
        secondary=wildcard_imports,
        primaryjoin=id == wildcard_imports.c.scope_id,
        secondaryjoin=id == wildcard_imports.c.imported_scope_id,
        order_by=wildcard_imports.c.import_order,
        lazy="select"
    )

    def __repr__(self):
        return f"<ScopeORM(id='{self.id}', type='{self.scope_type}')>"


class SymbolORM(Base):
    """
    SQLAlchemy ORM model for Symbol.
    """
    __tablename__ = 'symbols'

    # Primary key - the qualified name
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    symbol_type = Column(String, nullable=False, index=True)

    # Foreign keys
    defining_scope_id = Column(
        String,
        ForeignKey('scopes.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    assigned_to_id = Column(
        String,
        ForeignKey('symbols.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    instance_scope_id = Column(
        String,
        ForeignKey('scopes.id', ondelete='SET NULL'),
        nullable=True
    )

    # JSON metadata for flexibility
    metadata_json = Column('metadata', JSON, default={})

    # Relationships
    defining_scope = relationship(
        "ScopeORM",
        back_populates="symbols",
        foreign_keys=[defining_scope_id],
        lazy="joined"  # Eager load the defining scope
    )

    assigned_to = relationship(
        "SymbolORM",
        remote_side=[id],
        foreign_keys=[assigned_to_id],
        backref="assigned_from_symbols",
        lazy="joined"
    )

    instance_scope = relationship(
        "ScopeORM",
        foreign_keys=[instance_scope_id],
        lazy="select"
    )

    def __repr__(self):
        assignment = f" -> {self.assigned_to_id}" if self.assigned_to_id else ""
        return (
            f"<SymbolORM(id='{self.id}', type='{self.symbol_type}'"
            f"{assignment})>"
        )
