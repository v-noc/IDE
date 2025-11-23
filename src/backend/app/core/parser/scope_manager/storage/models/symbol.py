from enum import Enum
from sqlalchemy import Column, String, ForeignKey, Boolean, Index, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class SymbolType(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"
    CAPTURED_CLOSURE = "captured_closure"
    PARAMETER = "parameter"
    OBJECT_INSTANCE = "object_instance"  # For class instances


class SymbolModel(Base):
    __tablename__ = 'symbols'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    # 'variable', 'function', 'class', etc.
    symbol_type = Column(String, nullable=False, index=True)

    # Foreign Key to the scope where this symbol is defined.
    defining_scope_id = Column(
        String,
        ForeignKey('scopes.id', ondelete='CASCADE'),
        nullable=False,
    )

    defines_scope_id = Column(
        String,
        ForeignKey('scopes.id', ondelete='CASCADE'),
        nullable=True,

    )

    # --- Links for Contextual Analysis ---

    # For aliases: if `x = my_func`, this links symbol 'x' to symbol 'my_func'.
    assigned_to_id = Column(
        String,
        ForeignKey('symbols.id', ondelete='SET NULL'),
        index=True,
    )

    # For object instances:
    # if `obj = MyClass()`, this links symbol 'obj' to a unique scope
    # that will hold its instance attributes (e.g., obj.name).
    instance_scope_id = Column(
        String,
        ForeignKey('scopes.id', ondelete='CASCADE'),
        unique=True,
    )

    # For closures: Links a returned function to the runtime frame it captured.
    captured_frame_id = Column(
        String,
        ForeignKey('call_frames.id', ondelete='SET NULL'),
    )

    # For closures and object instances: Links back to the original symbol.
    # - For CAPTURED_CLOSURE: links to the original FUNCTION symbol
    # - For OBJECT_INSTANCE: links to the original CLASS symbol
    # This enables: function.closure_instances or class_symbol.object_instances
    original_symbol_id = Column(
        String,
        ForeignKey('symbols.id', ondelete='SET NULL'),
        index=True,
        nullable=True
    )

    # --- Staleness Tracking for Resync ---
    is_stale = Column(Boolean, default=False, index=True)
    stale_reason = Column(String, nullable=True)
    stale_since = Column(String, nullable=True)  # ISO datetime string

    # Flexible storage for complex data like MRO lists, decorators, etc.
    # Using 'name=' param because 'metadata' is reserved in SQLAlchemy
    attrs = Column('attrs', JSON, default={})

    # 1. Relationship for defining_scope (FIXED)
    defining_scope = relationship(
        "ScopeModel",
        back_populates="symbols",
        # CRITICAL: Tells SA exactly which column to use for joining
        foreign_keys=[defining_scope_id]
    )

    # 2. Relationship for instance_scope (Optional, but recommended for clarity)
    instance_scope = relationship(
        "ScopeModel",
        # We don't back_populate to a list in ScopeORM because this is One-to-One
        foreign_keys=[instance_scope_id]
    )

    defines_scope = relationship(
        "ScopeModel",
        back_populates="symbol",
        foreign_keys=[defines_scope_id]
    )

    # Relationship for tracking derived symbols (closures, instances)
    original_symbol = relationship(
        "SymbolModel",
        foreign_keys=[original_symbol_id],
        remote_side=[id],
        backref="derived_symbols"
    )
    # Usage:
    # - function.derived_symbols -> all closures created from this function
    # - class_symbol.derived_symbols -> all instances created from this class
    # - closure.original_symbol -> the original function
    # - instance.original_symbol -> the original class

    # The most important index for performance!
    __table_args__ = (
        Index(
            'ix_symbol_scope_name',
            'defining_scope_id',
            'name',
            unique=True,
        ),
    )
