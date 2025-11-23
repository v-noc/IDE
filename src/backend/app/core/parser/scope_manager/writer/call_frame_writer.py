# storage/writers/call_frame_writer.py
"""
CallFrameWriter - Handles creation and persistence of call frames.
Part of the Writer Layer in the call graph architecture.
"""

import uuid
from typing import Optional

from app.core.parser.scope_manager.storage.repository.repos import ScopeManagerRepository
from app.core.parser.scope_manager.storage.models import CallFrameModel, SymbolType


class CallFrameWriter:
    """
    Writer for CallFrame entities.
    Separates write operations from core service logic, making transactions explicit.
    """

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def create_frame(
        self,
        callee_symbol_id: str,
        execution_scope_id: str,
        parent_frame_id: Optional[str] = None,
        call_depth: int = 0
    ) -> str:
        """
        Build and persist a complete call frame with all required relationships.

        Args:
            callee_symbol_id: ID of the function/method being called
            execution_scope_id: ID of the scope holding this frame's locals
            parent_frame_id: ID of the calling frame (None for root calls)
            call_depth: Depth in the call stack (for recursion detection)

        Returns:
            The ID of the created frame

        Raises:
            ValueError: If validation fails
        """
        # Generate unique ID
        frame_id = str(uuid.uuid4())

        # Build ORM entity
        frame = CallFrameModel(
            id=frame_id,
            callee_symbol_id=callee_symbol_id,
            execution_scope_id=execution_scope_id,
            parent_frame_id=parent_frame_id,
            call_depth=call_depth,
            return_symbol_id=None  # Set later via complete_frame
        )

        # Validate before persisting
        self._validate_frame(frame)

        # Persist to database
        self.repo.call_frames.create(frame)

        return frame_id

    def complete_frame(
        self,
        frame_id: str,
        return_symbol_id: Optional[str] = None
    ) -> None:
        """
        Update a frame with its return value.

        Args:
            frame_id: ID of the frame to update
            return_symbol_id: ID of the symbol returned (None if no return)
        """
        frame = self.repo.call_frames.get_by_id(frame_id)
        if not frame:
            raise ValueError(f"Frame {frame_id} not found")

        frame.return_symbol_id = return_symbol_id
        # SQLAlchemy auto-tracks changes, will be committed by service

    def _validate_frame(self, frame: CallFrameModel) -> None:
        """
        Validation before persistence.

        Raises:
            ValueError: If validation fails
        """
        if frame.call_depth < 0:
            raise ValueError("Call depth cannot be negative")

        if frame.call_depth > 1000:
            raise ValueError(
                f"Call depth suspiciously high ({frame.call_depth}) - "
                f"possible infinite recursion"
            )

        # Verify callee symbol exists
        callee = self.repo.symbols.get_by_id(frame.callee_symbol_id)
        if not callee:
            raise ValueError(
                f"Callee symbol {frame.callee_symbol_id} not found"
            )

        # Verify callee is callable
        if callee.symbol_type not in (SymbolType.FUNCTION, SymbolType.CLASS, SymbolType.CAPTURED_CLOSURE):
            raise ValueError(
                f"Cannot call symbol '{callee.name}' of type {callee.symbol_type}. "
                f"Only functions and classes are callable."
            )

        # Verify execution scope exists
        scope = self.repo.scopes.get_by_id(frame.execution_scope_id)
        if not scope:
            raise ValueError(
                f"Execution scope {frame.execution_scope_id} not found"
            )
