from sqlalchemy import Column, String, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class CallFrameModel(Base):
    """Represents a single, runtime invocation of a function."""
    __tablename__ = 'call_frames'
    id = Column(String, primary_key=True)

    # What function was actually called in this frame?
    callee_symbol_id = Column(String, ForeignKey(
        'symbols.id', ondelete='CASCADE'), index=True)

    # The unique scope that holds this frame's local variables and arguments.
    execution_scope_id = Column(String, ForeignKey(
        'scopes.id', ondelete='CASCADE'), unique=True)

    # What this specific invocation returned
    return_symbol_id = Column(String, ForeignKey(
        'symbols.id', ondelete='SET NULL'), nullable=True)

    # Call depth for recursion detection
    call_depth = Column(JSON, default=0)

    # --- Staleness Tracking for Resync ---
    is_stale = Column(Boolean, default=False, index=True)
    stale_reason = Column(String, nullable=True)
    needs_recompute = Column(Boolean, default=False, index=True)
    original_callee_hash = Column(
        String, nullable=True)  # Function signature hash
    last_verified = Column(String, nullable=True)  # ISO datetime string

    # SQLAlchemy relationships for navigation
    callee_symbol = relationship(
        "SymbolModel",
        foreign_keys=[callee_symbol_id],
        backref="call_frames_as_callee"
    )

    execution_scope = relationship(
        "ScopeModel",
        foreign_keys=[execution_scope_id],
        backref="call_frame"
    )

    return_symbol = relationship(
        "SymbolModel",
        foreign_keys=[return_symbol_id],
        backref="call_frames_as_return"
    )

    # Call sites where this frame is the callee
    call_sites_as_callee = relationship(
        "CallSiteModel",
        back_populates="callee_frame",
        cascade="all, delete-orphan",
        foreign_keys="CallSiteModel.callee_frame_id",
    )


class CallSiteModel(Base):
    """Represents the static edge: 'A calls B'."""
    __tablename__ = 'call_sites'
    id = Column(String, primary_key=True)

    # In which runtime context did the call happen?
    caller_scope_id = Column(String, ForeignKey(
        'scopes.id', ondelete='CASCADE'), index=True)

    # Which function was called at this site?
    callee_frame_id = Column(String, ForeignKey(
        'call_frames.id', ondelete='CASCADE'), index=True)

    # --- Staleness Tracking for Resync ---
    is_stale = Column(Boolean, default=False, index=True)
    verified_valid = Column(Boolean, default=False)

    # SQLAlchemy relationships for navigation
    caller_scope = relationship(
        "ScopeModel",
        foreign_keys=[caller_scope_id],
        back_populates="call_sites_as_caller"
    )

    callee_frame = relationship(
        "CallFrameModel",
        foreign_keys=[callee_frame_id],
        back_populates="call_sites_as_callee"
    )
